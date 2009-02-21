#dailypost

dailypost is an `/etc/motd` manager. It lets you create and edit entries
without having to manually edit the `motd` (message of the day) file itself. It
is also kind enough to format your `motd` file so that only the latest entries
show up. 

#Why use dailypost?

The `motd` file is the time tested way to communicate with your shell users.
For the same reason, it also acts as a living record what's happened in your
systems over time. In order to learn from your history, you've got to
first start recording it!

## Better than versioning
Sure, you could just check your whole `/etc` directory into SVN. But then you'd
have to manually edit your `motd` each time and style it so it looks nice.
You also have to think about how many entries you want to keep around
at a given time: another manual effort. Well, with dailypost, you get a
plain-text archive of all your old `motd` entries and you don't ever
have to worry about the actual `motd` file itself.

## Pretty in plaintext

dailypost knows that even in plain-text, you've got to dress to impress.
dailypost indents your paragraphs, centers your headers and aligns your
signatures. It even lets you pick out the indent values and everything.

## Reminisce

Want to pass your sysadmin history on to coming generations? dailypost keeps a
detailed record of all entires that go into your `motd` over the ages.

What's more, dailypost does not use a crazy binary serialization format for
storing archived entries. It's just plain-text. (Although, you have to use
dailypost if you want to edit these entries.) Remember that time when we had
the power outage and the UPS started blowing out black smoke? Just grep your
motd archive it will come right up.

## License

Released under the MIT License. See LICENSE for full text.
