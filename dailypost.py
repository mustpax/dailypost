#!/usr/bin/python
"""
MOTD entry manager v0.2.
Mustafa Paksoy. March 2008.
"""

# TODO remove empty date directories

from datetime import date, timedelta
from textwrap import TextWrapper
from tempfile import NamedTemporaryFile
from optparse import OptionParser
from config import Config
import readline, re, os, sys, string, subprocess

# CONSTANTS
EMPTY_REGEX=re.compile(r'^\s*$')
Config['dateTemplate'] = string.Template(Config['dateFormat'])

def gimmeRoom(n):
  "Return string with n space characters."
  ret=[]
  for i in range(n):
    ret.append(' ')
  return ''.join(ret)

def formatDate(date):
  "Return formatted string for given datetime.date object"
  return Config['dateTemplate'].safe_substitute(day=date.day, month=date.month, year=date.year)

class Entry:
  FILE_HEADER='WARNING: This file is automatically generated. '+\
              'Do not modify it manually. Format id: 0001'
  SPLIT_RE=re.compile(r'\n{2,}')
  NEWLINE_RE=re.compile(r'\n')

  @staticmethod
  def getNewFromUser():
    return Entry().updateFromUser()

  @staticmethod
  def getFromFile(fileHandle):
    "Parse contents of file and create a Entry out of the values."
    assert fileHandle.readline().rstrip() == Entry.FILE_HEADER
    author=fileHandle.readline().rstrip()
    dateobj=Entry.parseDate(fileHandle.readline().rstrip())
    title=fileHandle.readline().rstrip()
    text=[line.rstrip() for line in fileHandle]
    return Entry(author=author, title=title, date=dateobj, text=text)

  @staticmethod
  def parseDate(datestr):
    m=Config['dateRegex'].match(datestr)
    if not m:
      error(ValueError, 'Invalid date string: ' + datestr)
    return date(day=int(m.group('day')), month=int(m.group('month')), year=int(m.group('year')))

  def __init__(self, author=None, title=None, date=None, text=None):
    self.__author = author
    self.__title = title
    self.__date = date
    self.__text = text

  def updateFromUser(self):
    self.__author = Entry.__inputWithDefault('Author (leave empty to use your username): ', 
                                              self.__author)
    self.__title = Entry.__inputWithDefault('Entry title: ', self.__title)

    if EMPTY_REGEX.match(self.__author):
      if ('SUDO_USER' in os.environ):
        self.__author = os.environ['SUDO_USER']
      elif ('USER' in os.environ):
        self.__author = os.environ['USER']
      else:
        self.__author = 'unknown'
  
    datestr = None
    if self.__date is not None:
      datestr = formatDate(self.__date)
    datestr = self.__inputWithDefault('Date mm/dd/yyyy (leave empty for today): ', datestr)

    if EMPTY_REGEX.match(datestr):
      self.__date = date.today()
    else:
      self.__date = Entry.parseDate(datestr)

    self.__text = Entry.__editBody(self.__text)

    return self

  def writeToFile(self, fileHandle):
    """
    Writes current entry to the file handle.
    """
    fileHandle.write(Entry.FILE_HEADER)
    fileHandle.write('\n')
    fileHandle.write(self.__author)
    fileHandle.write('\n')
    fileHandle.write(formatDate(self.__date))
    fileHandle.write('\n')
    fileHandle.write(self.__title)
    fileHandle.write('\n')
    for line in self.__text:
      fileHandle.write(line)
      fileHandle.write('\n')

  def getDate(self):
    return self.__date
  
  # Input and formatting helper methods beyond here.
  @staticmethod
  def __inputWithDefault(prompt=None, default=None):
    if (default is not None):
      def hook():
        readline.insert_text(default)
        readline.redisplay()
      readline.set_pre_input_hook(hook)
   
    ret = raw_input(prompt)
   
    if (default is not None):
      readline.set_pre_input_hook() # clear hook
    return ret

  @staticmethod
  def __editBody(text=None):
    tmpEntry = NamedTemporaryFile('w', 0)
    if (text is not None):
      for line in text:
        tmpEntry.write(line)
        tmpEntry.write('\n')

    editor = Config['defaultEditor']
    if ('EDITOR' in os.environ):
      editor = os.environ['EDITOR']
    subprocess.call([editor, tmpEntry.name])

    # Open the file again to get new contents. I don't think we can do this in Windows.
    newTmpEntry = open(tmpEntry.name, 'r')
    text=[line.rstrip().lstrip() for line in newTmpEntry]
    text='\n'.join(text)
    text=Entry.SPLIT_RE.split(text)
    text=[Entry.NEWLINE_RE.sub(' ',par) 
          for par in text 
            if (not(EMPTY_REGEX.match(Entry.NEWLINE_RE.sub(' ',par))))]
    newTmpEntry.close()
    tmpEntry.close()
    return text
  
  def __getHeader(self):
    ret=[]
    date = formatDate(self.__date)
    # apply indent on both sides, 2 center
    headerlen = Config['lineLength'] - 2 - 2 * Config['headerIndent']
    textlength = len(self.__title) + len(date)
    ret.append(gimmeRoom(Config['headerIndent']))
    ret.append(self.__title)
    ret.append(gimmeRoom((headerlen - textlength)/2))
    ret.append("::")
    ret.append(gimmeRoom((headerlen - textlength)/2))
    ret.append(date)
    return ''.join(ret)

  def __getBody(self):
    ret=[]
    indent=gimmeRoom(Config['bodyIndent'])
    wrapper = TextWrapper(initial_indent=indent, subsequent_indent=indent, \
              width=Config['lineLength']-Config['bodyIndent'])
    for par in self.__text:
      ret.append(wrapper.fill(par))
    return '\n\n'.join(ret)

  def __getFooter(self):
    ret=[]
    ret.append(gimmeRoom(Config['lineLength']-len(self.__author)-Config['footerRightIndent']))
    ret.append(self.__author)
    ret.append('\n')
    for sigline in Config['sig']:
      ret.append(gimmeRoom(Config['lineLength']-len(sigline)-Config['footerRightIndent']))
      ret.append(sigline)
      ret.append('\n')
    return ''.join(ret)
  
  def __str__(self):
    return '\n'.join([self.__getHeader(), \
                      self.__getBody(), \
                      self.__getFooter()])

class Archive:
  """
  The Archive class handles the storage of entries in the file system.
  Individual entries are stored in text files under the 'bydate/'
  directory. We also store symbolic links in the 'entries/'
  directory to allow individual entries to be refereced by
  their numeric id alone.
  """
  DIR_FORMAT = string.Template('$archivedir/$year/$month/$day')
  FILE_FORMAT = '%06d'
  FILE_REGEX = r'\d{6}'
  ID_DIR = 'entries'
  DATE_DIR = 'bydate'
  
  def __init__(self, rootdirpath):
    self.__root = rootdirpath
    self.__byid = os.path.join(rootdirpath, Archive.ID_DIR)
    self.__bydate = os.path.join(rootdirpath, Archive.DATE_DIR)

    # Create necessary sub directories
    for dir in [self.__root, self.__byid, self.__bydate]:
      if not os.path.isdir(dir):
        os.makedirs(dir)

    countfilepath = os.path.join(self.__byid, '.nextid')
    # create new file if there isn't one already
    if not os.path.isfile(countfilepath):
      cf = open(countfilepath, 'w')
      cf.write('1\n')
      cf.close()
    
    self.__countfile = open(countfilepath, 'r+w')

  def add(self, entry):
    id = self.__getNextId()
    self.saveEntry(id, entry)
    return id

  def update(self, id):
    if not self.hasId(id):
      error(ValueError, "Cannot find entry with id '%d' in archive." % id)

    link = open(self.__getIdFile(id), 'r')
    entry = Entry.getFromFile(link)
    link.close()
    entry.updateFromUser()
    self.saveEntry(id, entry)

  def delete(self, id):
    if not self.hasId(id):
      error(ValueError, "Cannot find entry %d in archive." % id)
    
    idlink = self.__getIdFile(id)
    realfile = os.path.abspath(os.path.realpath(idlink))
    bydatedir = os.path.abspath(self.__bydate)

    # Ensure that linked file is under the bydate directory. I've seen some
    # pretty nasty tricks being pulled with malicious symlinks.
    if os.path.commonprefix([realfile, bydatedir]) != bydatedir:
      error(ValueError, 'Entry %d is corrupted, cannot delete.' % id)

    os.unlink(idlink)
    os.unlink(realfile)

  def saveEntry(self, entryId, entry):
    targetfile = self.__getDateFile(entryId, entry.getDate())
    entryfile = open(targetfile, 'w')
    entry.writeToFile(entryfile)
    entryfile.close()
    self.__updateIdRef(entryId, entry.getDate())
  
  def __updateIdRef(self, id, date):
    idlink = self.__getIdFile(id)
    datefile = self.__getDateFile(id, date)
    if os.path.islink(idlink):
      if os.path.isfile(datefile):
        oldfile = os.path.abspath(os.path.realpath(idlink))
        if oldfile != datefile:
          # remove old target if no longer valid
          os.unlink(oldfile)
          # link is now broken remove it too
          os.unlink(idlink) # remove old link
        else:
          # link already pointing to the right file
          return

    # TODO use relative path for link for easy archive move
    os.symlink(datefile, idlink)

  def writeLatest(self, output=sys.stdout, num=Config['shownEntries']):
    """
    Write the latest 'num' entries to the given output file handle.
    Adds a footer indicating last modified date. Normally used to populate the motd file.
    """
    output.write(Config['motdHeader'].safe_substitute(update_date=formatDate(date.today())))
    i=0
    ret=[]
    for entry in self.walkEntries():
      if i >= num:
        break
      assert os.path.isfile(entry)
      fd = open(entry, 'r')
      #output.write(str(Entry.getFromFile(fd)))
      ret.append(str(Entry.getFromFile(fd)))
      fd.close()
      #output.write(Config['entrySeperator'])
      i+=1
    output.write(Config['entrySeperator'].join(ret))
    # TODO footer

  def walkEntries(self, dir=None):
    "Returns a generator that returns paths to entry files. Walks newest entries first."
    if dir is None:
      for path in self.walkEntries(self.__bydate):
        yield path
    else:
      rootfiles = os.listdir(dir)
      if len(rootfiles) > 0:
        rootfiles.sort(cmp=(lambda x,y: int(y)-int(x)))
        for file in rootfiles:
          if re.match(Archive.FILE_REGEX, file):
            yield os.path.join(dir,file)
          else:
            for subfile in self.walkEntries(os.path.join(dir,file)):
              yield subfile

  def hasId(self, entryid):
    "Returns true if entry with given id number exists."
    idlink = self.__getIdFile(entryid)
    if os.path.islink(idlink):
      entryfile = os.path.realpath(idlink)
      return os.path.isfile(entryfile)

    return False

  def __getDateDir(self, date):
    """
    Return the path for the directory that contains entries that belong to
    the given date. Creates the directory if it doesn't exist.
    """
    if date is None: return None
    ret=Archive.DIR_FORMAT.safe_substitute(archivedir=self.__bydate, year=date.year,
                                           day=date.day, month=date.month)
    if not os.path.isdir(ret):
      # Need to create directory
      os.makedirs(ret)
    return ret

  def __getDateFile(self, id, date):
    return os.path.abspath(os.path.join(self.__getDateDir(date), (Archive.FILE_FORMAT % id)))

  def __getIdFile(self, id):
    return os.path.abspath(os.path.join(self.__byid, (Archive.FILE_FORMAT % id)))

  def __getNextId(self):
    val = self.__countfile.readline().rstrip().lstrip()
    ret = int(val)
    self.__countfile.seek(0)
    self.__countfile.truncate()
    self.__countfile.write(str(ret + 1))
    self.__countfile.write('\n')
    self.__countfile.seek(0)
    return ret

def generatesome(arc):
  d=date.today()
  delta=timedelta(0)
  for i in range(3):
    e=Entry('John Doe', 'Lorem Ipsum', d, ["Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Vestibulum pulvinar elit at lectus. Nam consequat nunc a mauris. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Proin tortor. Nunc pellentesque facilisis orci. Etiam ornare sem nec ante. Praesent vehicula nisl ut sapien. Nam diam. Suspendisse potenti. Sed leo est, dapibus ac, porta ornare, sagittis id, est. Donec dapibus faucibus elit. Aliquam pretium. Vivamus viverra. Nam ante. Nulla feugiat, enim sit amet dapibus gravida, metus odio volutpat orci, elementum interdum leo nisi quis massa. Integer vitae mi eu quam placerat pretium. Quisque consequat dui a leo. Vivamus semper nulla nec odio. Suspendisse congue pretium arcu. Sed vitae libero vitae neque commodo blandit.", "Proin eu pede id lorem ultricies eleifend. Ut lobortis. Vivamus vestibulum diam a quam. Suspendisse consequat, tellus ultricies adipiscing convallis, nunc ligula facilisis erat, volutpat lacinia justo ligula id turpis. Praesent at mauris ut ante fringilla consectetuer. Integer non lacus. Nunc quis lorem. Quisque ligula. Vivamus quis urna vitae turpis dictum porttitor. Vivamus neque tellus, rutrum vel, bibendum vitae, sagittis a, ante. Vestibulum interdum convallis sapien. In pretium urna eu enim."])
    #print str(e)
    #e=Entry('John Doe', 'Lorem Ipsum', datetime.today(), None)
    #e.updateFromUser()
    #print str(e)
    arc.add(e)
    arc.add(e)
    d -= delta

def getOptionParser():
  parser = OptionParser(usage="usage: %prog [options] [entry id]")
  parser.set_defaults(mode='add')
  parser.add_option('-a', action='store_const', dest='mode', const='add', \
                    help='add new MOTD entry [default]')
  parser.add_option('-d', action='store_const', dest='mode', const='delete', \
                    help='edit old MOTD entry')
  parser.add_option('-e', action='store_const', dest='mode', const='edit', \
                    help='delete old MOTD entry')
  parser.add_option('-n', action='store_const', dest='mode', const='none', \
                    help='do not modify any entries, just update MOTD file')
  parser.add_option('-u', action='store_true', dest='update', default=True, \
                    help='update MOTD file with latest entries [default]')
  parser.add_option('-U', action='store_false', dest='update', \
                    help='do not update MOTD file')
  parser.add_option('-y', action='store_true', dest='alwaysYes', default=False, \
                    help='do not ask for confirmation before making potentially destructive changes')
  parser.add_option('-D', action='store_true', dest='debugMode', default=False, \
                    help='run in debug mode')
  parser.add_option('-O', action='store_true', dest='motdToStdout', default=False, \
                    help='print new MOTD to standard output, do not modify the actual file')
  return parser


def error(exception, msg):
  """
  Display error message.
  When in debug mode will throw the given exception with the given message.
  Otherwise, it will simply print given message out to stderr.
  """
  if Config['debugMode']:
    raise exception(msg)
  sys.stderr.write('Error: ')
  sys.stderr.write(msg)
  sys.stderr.write('\n')
  sys.exit()

def confirm(msg=""):
  """
  Display the given message and ask for a confirmation. All answers other than
  "y" or "yes" are taken to be negative. Case insensitive, so "yes" and "YeS" are
  both affirmative.
  Return true on "y" or "yes", false otherwise.
  """
  if Config['alwaysYes']: return True

  msg += " (y/n) "
  return raw_input(msg).lower() in ['y', 'yes']

def main():
  def getid(args):
    "Parse the entry id out of the arguments."  
    if len(args) == 0:
      error(ValueError, 'Missing argument: entry id.')

    return int(args[0])

  arc = Archive(Config['archiveDir'])
  (options, args) = getOptionParser().parse_args()

  mode=options.mode
  Config['debugMode'] = options.debugMode
  Config['alwaysYes'] = options.alwaysYes

  if (mode == 'add'):
    entry = Entry.getNewFromUser()
    print 'Saved new entry %d.' % arc.add(entry)
  elif (mode == 'delete'):
    entryid = getid(args)
    arc.delete(entryid)
    print 'Entry %d permanently deleted.' % entryid
  elif (mode == 'edit'):
    entryid = getid(args)
    print 'Editing entry %d.' % entryid
    arc.update(entryid)
    print 'Entry %d saved.' % entryid
  elif (mode == 'none'):
    pass
  else:
    error(ValueError, 'Invalid edit mode: ' + mode)

  if (options.update):
    if options.motdToStdout:
      arc.writeLatest()
    elif confirm('Overwrite old MOTD file "%s"?' % Config['motdFile']):
      print 'Writing new MOTD file.',
      # TODO overwrite warning
      motdfile = open(Config['motdFile'], 'w')
      arc.writeLatest(motdfile)
      print 'Done.'
      motdfile.close()
    else:
      print 'Cancelled updating MOTD file.'

if __name__ == '__main__':
  main()
