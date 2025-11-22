from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import app.keyboards as kb
import datetime
from app.database import get_db_connection

router = Router()

class Tour(StatesGroup):
    location1 = State()
    location2 = State()
    location3 = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    conn = get_db_connection()
    
    cursor = conn.execute('''
        SELECT tour_completed_at FROM user_tour_progress WHERE user_id = ?
    ''', (message.from_user.id,))
    user_data = cursor.fetchone()
    
    if user_data and user_data['tour_completed_at']:
        await message.answer(
            f"С возвращением, {message.from_user.first_name}! 👋🏼\n"
            "Ты уже успешно прошел тур! 🏆\n\n"
            "Можешь посмотреть таблицу лидеров:",
            reply_markup=kb.restart
        )
    else:
        conn.execute('''
            INSERT OR REPLACE INTO user_tour_progress 
            (user_id, username, first_name, last_name, tour_started_at) 
            VALUES (?, ?, ?, ?, ?)
        ''', (
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name,
            datetime.datetime.now().isoformat()
        ))
        conn.commit()
        
        await message.answer(
            f"Привет, {message.from_user.first_name}! 👋🏼\n"
            "Ты посетишь 3 локации и узнаешь немного истории 🏙️\n\n"
            "Нажми кнопку, чтобы начать:",
            reply_markup=kb.start
        )
    
    conn.close()

@router.callback_query(F.data == "start_tour")
async def start_tour(callback : CallbackQuery, state: FSMContext):
    conn = get_db_connection()
    conn.execute('''
        UPDATE user_tour_progress 
        SET tour_started_at = ? 
        WHERE user_id = ?
    ''', (datetime.datetime.now().isoformat(), callback.from_user.id))
    conn.commit()
    conn.close()
    
    photo = FSInputFile("images/1.jpg")
    await callback.answer()
    await callback.message.answer_photo(
        photo=photo,
        caption="Загадка №1:\n"
                "❓ 2 + 2\n\n"
                "Напиши свой ответ в чат:",
    )
    await state.set_state(Tour.location1)

@router.callback_query(F.data == "table_lider")
async def table(callback: CallbackQuery):
    await callback.answer()

    conn = get_db_connection()
    
    # Получаем топ лидеров
    cursor = conn.execute('''
        SELECT username, first_name, completion_time_seconds
        FROM user_tour_progress 
        WHERE tour_completed_at IS NOT NULL 
        ORDER BY completion_time_seconds ASC 
        LIMIT 3
    ''')
    leaders = cursor.fetchall()
    
    # Формируем таблицу лидеров
    if leaders:
        leader_text = "🏆 <b>Таблица лидеров</b>\n\n"
        medals = ["🥇", "🥈", "🥉"]
        
        for i, leader in enumerate(leaders):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            name = leader['username'] or leader['first_name'] or "Аноним"
            time_seconds = leader['completion_time_seconds']
            
            # Форматируем время
            if time_seconds < 60:
                time_str = f"{time_seconds} сек."
            elif time_seconds < 3600:
                minutes = time_seconds // 60
                seconds = time_seconds % 60
                time_str = f"{minutes} мин. {seconds} сек."
            else:
                hours = time_seconds // 3600
                minutes = (time_seconds % 3600) // 60
                time_str = f"{hours} ч. {minutes} мин."
            
            leader_text += f"{medal} {name} - {time_str}\n"
        
        # ИНФОРМАЦИЯ О ТЕКУЩЕМ ПОЛЬЗОВАТЕЛЕ
        cursor = conn.execute('''
            SELECT completion_time_seconds
            FROM user_tour_progress 
            WHERE user_id = ? AND tour_completed_at IS NOT NULL
        ''', (callback.from_user.id,))
        
        user_data = cursor.fetchone()
        
        if user_data:
            user_time = user_data['completion_time_seconds']
            
            # Форматируем время пользователя
            if user_time < 60:
                user_time_str = f"{user_time} сек."
            elif user_time < 3600:
                minutes = user_time // 60
                seconds = user_time % 60
                user_time_str = f"{minutes} мин. {seconds} сек."
            else:
                hours = user_time // 3600
                minutes = (user_time % 3600) // 60
                user_time_str = f"{hours} ч. {minutes} мин."
            
            # Получаем место пользователя
            cursor = conn.execute('''
                SELECT COUNT(*) as user_rank
                FROM user_tour_progress 
                WHERE tour_completed_at IS NOT NULL 
                AND completion_time_seconds < ?
            ''', (user_time,))
            rank_data = cursor.fetchone()
            user_rank = rank_data['user_rank'] + 1 if rank_data else 1
            
            # Получаем общее количество игроков
            cursor = conn.execute('''
                SELECT COUNT(*) as total 
                FROM user_tour_progress 
                WHERE tour_started_at IS NOT NULL
            ''')
            total_data = cursor.fetchone()
            total_players = total_data['total'] if total_data else 0
            
            leader_text += f"\n──────────────\n"
            leader_text += f"<b>Твой результат:</b>\n"
            leader_text += f"🏅 Место: {user_rank} из {total_players}\n"
            leader_text += f"⏱ Время: {user_time_str}"
        else:
            leader_text += f"\n──────────────\n"
            leader_text += f"<i>Ты еще не прошел тур 😊\nПройти можно по кнопке ниже!</i>"
            
    else:
        leader_text = "🏆 <b>Таблица лидеров</b>\n\nПока нет лидеров. Будь первым! 🚀"
    
    conn.close()
    await callback.message.answer(leader_text, parse_mode="HTML")

@router.message(Tour.location1)
async def process_location1(message: Message, state: FSMContext):
    user_answer = message.text.lower().strip()
    if user_answer == "4":
        await message.answer("✅ Правильно! Молодец!\n\nПереходим ко второй локации...")
        await state.update_data(location1_answer=message.text)

        photo = FSInputFile("images/2.jpg")
        await message.answer_photo(
            photo=photo,
            caption="Загадка №2:\n"
                    "❓ 2 + 1\n\n"
                    "Напиши свой ответ в чат:",
        )
        await state.set_state(Tour.location2)
    else:
        await message.answer("❌ Неправильно! Попробуй еще раз.")

@router.message(Tour.location2)
async def process_location2(message: Message, state: FSMContext):
    user_answer = message.text.lower().strip()
    if user_answer == "3":
        await message.answer("✅ Правильно! Молодец!\n")
        await state.update_data(location2_answer=message.text)

        photo = FSInputFile("images/3.jpg")
        await message.answer_photo(
            photo=photo,
            caption="Загадка №3:\n"
                    "❓ 1 + 4\n\n"
                    "Напиши свой ответ в чат:",
        )
        await state.set_state(Tour.location3)
    else:
        await message.answer("❌ Неправильно! Попробуй еще раз.")

@router.message(Tour.location3)
async def process_location3(message: Message, state: FSMContext):
    user_answer = message.text.lower().strip()
    if user_answer == "5":
        conn = get_db_connection()
        
        cursor = conn.execute(
            'SELECT tour_started_at FROM user_tour_progress WHERE user_id = ?',
            (message.from_user.id,)
        )
        user_data = cursor.fetchone()
        
        completion_time = 0
        if user_data and user_data['tour_started_at']:
            start_time = datetime.datetime.fromisoformat(user_data['tour_started_at'])
            end_time = datetime.datetime.now()
            completion_time = int((end_time - start_time).total_seconds())
            
            conn.execute('''
                UPDATE user_tour_progress 
                SET tour_completed_at = ?,
                    completion_time_seconds = ?
                WHERE user_id = ?
            ''', (
                end_time.isoformat(),
                completion_time,
                message.from_user.id
            ))
            conn.commit()
        conn.close()

        await message.answer(
            "🎉 Поздравляю! Ты успешно прошел все локации!\n\n"
            "Спасибо за участие в экскурсии! 🏆",
            reply_markup = kb.restart
        )
        await state.clear()

    else:
        await message.answer("❌ Неправильно! Попробуй еще раз.")