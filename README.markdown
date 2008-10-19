#dailypost

dailypost is an `/etc/motd` manager. It lets you create and edit entries
without having to manually edit the `motd` (message of the day) file itself. It
is also kind enough to format your `motd` file so that only the latest 3
entries show up (or however many you want). Does pretty things like paragraph
indents and plain text styling to boot.

#Why use dailypost?

## Better than versioning

The `motd` file is the time tested way to communicate with your shell users.
For the same reason, it also acts as a living record what's happened in your
system over time. Especially for small student run shell account shops, like
the kind I used to work in, it's very important to retain this *institutional
memory*.

You could just check your whole `/etc` directory into SVN. But then you'd have
to manually edit your `motd` each time and style it so it looks sort of the
same. You also have to think about how many entries you want to keep around at
a given time: another manual effort. Well, will dailypost, you get a plain-text
searchable archive of all your old `motd` entries and you don't ever have to
worry about the actual file itself.

## Pretty

dailypost knows that even in plain-text, you've got to dress to kill. dailypost
indents your paragraphs, centers your headers and aligns your signatures. It
even lets you pick out the indent values and everything.

## Reminisce

Want to pass your sysadmin history on to coming generations? dailypost keeps a
detailed record of all entires that go into your `motd` over the ages.

What's more, dailypost does not use any sort of crazy binary serialization when
storing archived entries. It's just plain-text. (Although, you have to use
dailypost if you want to edit these entries.) Remember that time when we had
the power outage and the UPS started blowing out black smoke? Just grep your
motd archive it will come right up.
