
# dl-legistar-meeting-attachments

A commandline tool to download all attached documents for a given meeting, as listed on web pages created by the [Granicus company's online software tool, Legistar/Agenda LE](https://granicus.com/product/agenda-management-legistar/)

### What it does

1. access a public "meeting details" page for a given meeting, using a URL you provide
2. go through each agenda item linked from that page. For each agenda item:
    a. ensure there is a directory with that item's ID under the local directory you provide; if there is not yet such a directory, create one
    b. identify all documents attached to the agenda item
    c. for any of these documents that do not appear in the local directory, download them to the local directory

By first checking for the existence of local directories and files, this script is "idempotent", meaning it is designed to ensure a consistent result, whether you run it once or several times, and even if new agenda items are added, or new documents are attached to agenda items.

*Note that if a document is replaced by one with an identical name, the script will not currently catch this, and the old document will remain in the local directory.*

### Usage

```
python dl-legistar-meeting-attachments.py [-h] [-o local_output_directory] legistar_meeting_details_url

-h
optional argument; print usage to help user use this tool

-o local_output_directory
optional argument; will default to current directory from which the script is run

legistar_meeting_details_url
required argument; the "meeting details" page for the given meeting
```

### Example

```
python dl-legistar-meeting-attachments.py -o "/Users/ben/Documents/council meetings/2026/20261008/" 'https://somervillema.legistar.com/MeetingDetail.aspx?ID=1428403&GUID=FB9C9F45-61B5-41FE-9B09-0936B8BE539E&Options=info%7C&Search='
```

This example will access the public web page <https://somervillema.legistar.com/MeetingDetail.aspx?ID=1428403&GUID=FB9C9F45-61B5-41FE-9B09-0936B8BE539E&Options=info%7C&Search=> (a "meeting details" page), and go through all of the agenda items, opening each and downloading all of their attached documents to the user's local directory `/Users/ben/Documents/council meetings/2026/20261008/` .

*Note that you may need to enclose your local directory path and/or Legistar URLs with single quotes or double quotes, to accommodate any spaces and special characters in the directory paths or URLs.*

The script will create subdirectories named for the item numbers, like `/Users/ben/Documents/council meetings/2026/20261008/26-1454` , `/Users/ben/Documents/council meetings/2026/20261008/26-1455` , etc.

### Requirements

Requires that python 3 is installed locally, and that your python 3 install has the playwright module installed. Make sure that when you run

```
python --version
```

the output is something like

```
Python 3.x.x
```

If it isn't, search online for instructions for installing python 3 on your computer.
