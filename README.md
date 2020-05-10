# plenumsbot

A bot that is looking after our wiki and creates the pages for the coming plenary and sends the protocols.

## Dependencies

[Dokuwiki](https://dokuwiki.org) must have installed the [GOTO](https://dokuwiki.org/plugin:goto) plugin. The XML-RPC API has to be activated in the settings. Otherwise the bot won't be able to communicated with the wiki.

## Usage

`./plenumsbot.py`

There are no commandline switches, yet.

## What's plenumsbot doing?

1. get the current date
1. calculate dates of last and next plenum according to the configured day of week in config.json
1. loads the protocol of last (calculated) plenum
1. if the end time is still "20:xx Uhr" it's considered the plenum didn't take place
   1. topics are extracted from the last protocol
1. if the end time is set to a valid time it's considered the plenum took place and nothing (except upcoming events) has to be carried over
   1. A blank protocol is created from a given template
1. events are extraced from last plenum and events in the past are dropped from the list
1. the topics and the upcoming events are filled in a template to create the protocol template for the next plenum
1. the page is created in the wiki and populated with the contents
1. a link (if not existing) is inserted into the list of protocols
1. the redirect from "themensammlung" is updated to point to the page created for the next protocol

## config.json

- `wiki_url` : base url of your dokuwiki installation
- `wiki_user` : user the bot uses to login to the wiki
- `wiki_password` : the password for the given user
- `namespace` : the namespace in which the protocols are located
- `indexpage` : the page holding a list of all plenum protocols
- `redirectpage` : name of the page redirecting to the upcoming protocol
- `plenum_day_of_week`: the day of week on which the plenum takes place (0=Monday, 1=Tuesday, 2=Wednesday…)
