#!/usr/bin/python
import argparse
import json


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description='Convert ChatGPT export to LM Studio conversations')
    parser.add_argument('file', default='conversations.json',
                        type=argparse.FileType('r'))
    return parser


def main():
    args = build_arg_parser().parse_args()
    export = json.load(args.file)

    remove = str.maketrans('', '', '')

    for chat in export:
        obj = {
            'name': chat['title'],
            'createdAt': int(chat['create_time']),
            'systemPrompt': '',
            'messages': [],
            'notes': [
                f'ChatGPT ID: {chat['id']}'
            ]
        }

        if not 'client-created-root' in chat['mapping']:
            continue

        id = chat['mapping']['client-created-root']['children'][0]
        while True:
            item = chat['mapping'][id]
            msg = item['message']
            if msg:
                role = msg['author']['role']
                parts = msg['content'].get('parts', [])

            if len(parts) == 1 and parts[0] == '':
                pass
            elif msg['content'].get('text') == '':
                pass
            elif role == 'system':
                for part in parts:
                    obj['systemPrompt'] += part
            elif role == 'tool':
                pass
            elif not msg['metadata'].get('is_visually_hidden_from_conversation'):
                result = {
                    'versions': [{
                        'type': 'singleStep',
                        'role': role,
                        'content': []
                    }],
                    'currentlySelected': 0,
                }
                if msg['content']['content_type'] in ('text', 'code'):
                    if parts:
                        for part in parts:
                            result['versions'][0]['content'].append({
                                'type': 'text',
                                'text': part.translate(remove).strip()
                            })
                    elif msg['content'].get('text'):
                        result['versions'][0]['content'].append({
                            'type': 'text',
                            'text': msg['content']['text'].translate(remove).strip()
                        })
                elif msg['content']['content_type'] == 'multimodal_text':
                    result['versions'][0]['content'].append({
                        'type': 'image',
                        'filename': parts[0]['asset_pointer'][11:]
                    })

                if msg['metadata'].get('model_slug'):
                    result['versions'][0]['senderInfo'] = {
                        'senderName': msg['metadata']['model_slug']
                    }
                obj['messages'].append(result)

            if not item['children']:
                break

            id = item['children'][0]

        filename = f'{obj['createdAt']}.conversation.json'
        with open(filename, 'w') as f:
            json.dump(obj, f)


if __name__ == '__main__':
    main()
