from telethon import *;
from telethon import TelegramClient, events

# Введи сюда API ID и Hash твоего личного аккаунта
api_id = '******'
api_hash = '***************'

# ID чата, в который будут пересылаться сообщения 123456789
TARGET_CHAT_ID  = -100123456789

# ID топика в группе
TOPIC_ID = 12345  # ID топика 

# Создаем объект клиента для твоего аккаунта
client = TelegramClient('reply_client', api_id, api_hash)

# Словарь для сопоставления пересланных сообщений и оригинальных пользователей
message_mapping = {}

@client.on(events.NewMessage)
async def handle_incoming_message(event):
    try:
        sender_id = event.sender_id
        chat_id = event.chat_id

        # Получаем информацию о текущем аккаунте бота
        me = await client.get_me()

        # Если отправитель — это сам бот, не пересылаем сообщение
        if sender_id == me.id:
            return

        # Получаем сущность целевого чата
        target_chat = await client.get_input_entity(TARGET_CHAT_ID)

        # Проверка: если сообщение пришло из целевого чата (используем channel_id), то не пересылаем его
        if isinstance(target_chat, types.InputPeerChannel) and chat_id == TARGET_CHAT_ID:
            return

        # Определяем, является ли сообщение личным или групповым
        if event.is_private:
            # Личное сообщение — пересылаем его как обычно
            updates = await client(functions.messages.ForwardMessagesRequest(
                from_peer=event.chat_id,  # Чат, откуда пересылаем сообщение
                id=[event.message.id],    # ID сообщения, которое пересылаем
                to_peer=target_chat,      # Целевой чат
                top_msg_id=TOPIC_ID       # ID топика
            ))

            # Запоминаем отправителя и ID сообщения
            for update in updates.updates:
                if isinstance(update, types.UpdateMessageID):
                    message_mapping[update.id] = {
                        'sender_id': sender_id,
                        'chat_id': chat_id,
                        'message_id': event.message.id,  # Сохраняем ID исходного сообщения
                        'is_group': False
                    }

        elif event.is_group:
            # Если сообщение из группы, получаем название группы
            group_entity = await client.get_entity(chat_id)
            group_name = group_entity.title

            # Пересылаем сообщение в целевой чат с указанием группы
            updates = await client(functions.messages.ForwardMessagesRequest(
                from_peer=event.chat_id,  # Чат, откуда пересылаем сообщение
                id=[event.message.id],    # ID сообщения, которое пересылаем
                to_peer=target_chat,      # Целевой чат
                top_msg_id=TOPIC_ID       # ID топика
            ))

            # Запоминаем отправителя и ID сообщения
            for update in updates.updates:
                if isinstance(update, types.UpdateMessageID):
                    message_mapping[update.id] = {
                        'sender_id': sender_id,
                        'chat_id': chat_id,  # Сохраняем ID чата для ответа
                        'message_id': event.message.id,  # Сохраняем ID исходного сообщения
                        'group_name': group_name,
                        'is_group': True
                    }
            # Отправляем сообщение в целевой чат с указанием группы
                    await client.send_message(
                        target_chat,
                        f"Сообщение переслано из группы: {group_name}",
                        reply_to=TOPIC_ID
                    )

    except ValueError as e:
        print(f"Ошибка: {e}. Не удалось загрузить сущность отправителя.")
    except Exception as e:
        print(f"Общая ошибка при пересылке сообщения: {e}")


@client.on(events.NewMessage)
async def handle_reply(event):
    try:
        # Проверяем, что сообщение пришло из нужного чата
        target_chat = await client.get_entity(TARGET_CHAT_ID)  # Получаем целевой чат
        chat_target = f'-100{target_chat.id}'

        # Сравнение идентификаторов и проверка ответа
        if event.is_reply and str(event.chat_id) == chat_target:
            replied_message = await event.get_reply_message()

            if replied_message and replied_message.id in message_mapping:
                # Извлекаем информацию о пересланном сообщении
                message_info = message_mapping[replied_message.id]
                original_sender_id = message_info['sender_id']
                original_chat_id = message_info['chat_id']
                original_message_id = message_info['message_id']  # Получаем ID оригинального сообщения
                is_group = message_info.get('is_group', False)

                # Получаем информацию о том, кто ответил
                replier_entity = await client.get_entity(event.sender_id)
                replier_name = replier_entity.first_name if replier_entity.first_name else "Life-TV"

                if is_group:
                    # Если сообщение было из группы, отправляем ответ обратно в эту же группу с reply_to
                    await client.send_message(
                        original_chat_id,
                        f"Відвідь від оператора {replier_name}: \n{event.text}",
                        reply_to=original_message_id  # Ответ на исходное сообщение
                    )
                else:
                    # Если сообщение было личным, отправляем ответ напрямую пользователю
                    await client.send_message(
                        original_sender_id,
                        f"Відвідь від оператора {replier_name}: \n{event.text}",
                        reply_to=original_message_id  # Ответ на исходное сообщение
                    )

    except ValueError as e:
        print(f"Ошибка при обработке ответа: {e}")
    except Exception as e:
        print(f"Общая ошибка при обработке ответа: {e}")





async def main():
    try:
        await client.start()
        print("Клиент запущен и готов к работе.")
        

        await client.run_until_disconnected()
    except Exception as e:
        print(f"Ошибка во время выполнения клиента: {e}")


with client:
    client.loop.run_until_complete(main())