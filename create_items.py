#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json

DPT = {
    '1b': '1',
    '2b': '2',
    '4b': '3',
    '8b': '5',
    '1B': '5',
    '2B': '8',
    '3B': '232',
    '4B': '13',
    '14B': '16',
}

table = {
    ord(u'ä'): u'ae',
    ord(u'ö'): u'oe',
    ord(u'ü'): u'ue',
    ord(u'ß'): u'ss',
}


with open('alle.conf') as config:
    lines = config.readlines()

items = {}
addr_name_dpt_re = re.compile(r'^(\d+/\d+/\d+) (.*) (1b|2b|4b|8b|1B|2B|3B|4B|14B)$')
for line in lines:
    line = line.strip()
    item_match = addr_name_dpt_re.match(line)
    if item_match:
        room_match = re.search(r'(Wohnen|Bad|Büro|Küche|Essen|Technikraum|Ankleide|Schlafen|Flur|WC)',item_match.group(2))
        desc = re.sub(r'(Wohnen|Bad|Büro|Küche|Essen|Technikraum|Ankleide|Schlafen|Flur|WC)','', item_match.group(2)).strip()
        desc = re.sub(r'\s+', ' ', desc)
        room = room_match.group(1) if room_match else 'Allgemein'
        status = re.match('^Status (.*)', desc)
        switch = re.match('^Schalten (.*)', desc)
        level = re.match('^Dimmen (.*)', desc)
        up_down = re.match(r'(.*) Auf/Ab', desc)
        stop = re.match(r'(.*) Stop', desc)
        room_items = items.get(room,{ 'room' : True})
        if status:
            temp = room_items.get(status.group(1), {})
            temp['knx_status'] = item_match.group(1)
            temp['knx_dpt'] = item_match.group(3)
            room_items[status.group(1)] = temp
        elif switch:
            temp = room_items.get(switch.group(1), {})
            temp['knx_send'] = item_match.group(1)
            temp['knx_dpt'] = item_match.group(3)
            room_items[switch.group(1)] = temp
        elif up_down:
            temp = room_items.get(up_down.group(1), {})
            temp['up_down'] = {
                'knx_send': item_match.group(1),
                'knx_dpt': item_match.group(3)
            }
            room_items[up_down.group(1)] = temp
        elif stop:
            temp = room_items.get(stop.group(1), {})
            temp['stop'] = {
                'knx_send': item_match.group(1),
                'knx_dpt': item_match.group(3)
            }
            room_items[stop.group(1)] = temp
        elif level:
            temp = room_items.get(level.group(1), {})
            temp['level'] = {
                'knx_send': item_match.group(1),
                'knx_dpt': item_match.group(3)
            }
            room_items[level.group(1)] = temp
        else:
            temp = room_items.get(desc, {})
            temp['knx_reply'] = item_match.group(1)
            temp['knx_dpt'] = item_match.group(3)
            room_items[desc] = temp
        items[room] = room_items


def print_item(key, item, level):
    prefix = "\t" * (level)
    if isinstance(item, dict):
        translated_key = key.decode('utf8').translate(table)
        safe_key = re.sub(r'[^abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_]','_',translated_key)
        safe_key = re.sub(r'_+','_',safe_key)
        print "{}{}{}{}".format('\t'*(level-1), '[' *level , safe_key, ']' * level )
        print "{}name = {}".format(prefix, translated_key)

        if item.get('room'):
            print "{}sv_page = room".format(prefix)
        elif [key for key in item.keys() if 'knx' in key.lower()]:
            print "{}type = bool".format(prefix)
            print "{}visu_acl = rw".format(prefix)
            print "{}sv_widget = {{{{ basic.switch('item', 'item') }}}}".format(prefix)
        for a, b in item.iteritems():
            print_item(a, b, level + 1)
    else:
        if key == "knx_dpt":
            item = DPT[item]
        prefix = "\t" * (level-1)
        print "{}{} = {}".format(prefix, key, item)


for a,b in items.iteritems():
    print_item(a, b, 1)
