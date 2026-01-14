import asyncio
from aiogram import types, Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


BOT_TOKEN = 'YOUR_BOT_TOKEN'
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}


@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "job"}
    
    job_inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Sotuv menejeri", callback_data="job_sotuv")],
            [InlineKeyboardButton(text="SMM mutaxassisi", callback_data="job_smm")],
            [InlineKeyboardButton(text="Kopirayter", callback_data="job_copy")],
            [InlineKeyboardButton(text="Volontyor", callback_data="job_volunteer")],
        ]
    )

    video_note = FSInputFile("welcome.mp4")
    await message.answer_video_note(video_note=video_note)
    await message.answer(
        "Kompaniyamizni qaysi lavozimida ishlamoqchisiz:", 
        reply_markup=job_inline_keyboard
    )


@dp.callback_query()
async def handle_callbacks(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {}

    # Обработка выбора работы
    if callback.data.startswith("job_"):
        user_data[user_id]["job"] = callback.data
        user_data[user_id]["step"] = "name"
        
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "1/9. Ism-familyangizni yozing:\n\nMisol: Aziz Azizov"
        )
    
    # Обработка доступности
    elif callback.data.startswith("free_"):
        user_data[user_id]["availability"] = callback.data
        user_data[user_id]["step"] = "address"
        
        await callback.answer()
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "4/9. Yashash manzilingizni yozing:\n\n"
            "Misol: Toshkent shahar, Chilonzor tumani"
        )


@dp.message(F.text)
async def handle_text(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data:
        return

    step = user_data[user_id].get("step")

    # ШАГ 1: Имя
    if step == "name":
        user_data[user_id]["name"] = message.text
        user_data[user_id]["step"] = "phone"
        
        phone_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(
            "2/9. Telefon raqamingizni yozing:\n\nMisol: +998909998877",
            reply_markup=phone_keyboard
        )

    # ШАГ 2: Телефон
    elif step == "phone":
        phone = message.text.strip()
        digits = phone[1:] if phone.startswith("+") else phone

        if not digits.isdigit():
            await message.answer(
                "Telefon raqamingizni yozing:\n\nMisol: +998909998877"
            )
            return

        user_data[user_id]["phone"] = phone
        user_data[user_id]["step"] = "availability"
        
        availability_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Ha, to'liq bo'shman", callback_data="free_yes")],
                [InlineKeyboardButton(text="Ha, lekin to'liq emas", callback_data="free_partial")],
                [InlineKeyboardButton(text="Yo'q, bo'sh emasman", callback_data="free_no")],
            ]
        )
        photo = FSInputFile("schedule.jpg")
        await message.answer_photo(
            photo=photo,
            caption="3/9. Tog' darslaridan tashqari dasturimiz bo'ladigan sanlarda to'liq bo'shmisiz?",
            reply_markup=availability_keyboard
        )

    # ШАГ 4: Адрес
    elif step == "address":
        user_data[user_id]["address"] = message.text
        user_data[user_id]["step"] = "birthdate"
        await message.answer(
            "5/9. O'z tug'ilgan kuningizni 01.01.2000 formatda yozing:"
        )

    # ШАГ 5: Дата рождения
    elif step == "birthdate":
        birthdate = message.text.strip()

        if not (len(birthdate) == 10 and birthdate[2] == '.' and birthdate[5] == '.'):
            await message.answer(
                "Tug'ilgan kuningizni 01.01.2000 formatda yozing."
            )
            return

        user_data[user_id]["birthdate"] = birthdate
        user_data[user_id]["step"] = "video"
        
        video = FSInputFile("question_video.mp4")
        await message.answer_video_note(video_note=video)
        await message.answer("6/9. Video-vizitkangizni yuboring:")

    # ШАГ 7: Где учитесь/работаете
    elif step == "answer_7":
        user_data[user_id]["answer_7"] = message.text
        user_data[user_id]["step"] = "answer_8"
        await message.answer(
            "8/9. Oldin qaysi tashkilotlarda volontyorlik qilgansiz va tajribangiz haqida yozing:\n\n"
            "(Bitta xabarda yozing 📝)"
        )

    # ШАГ 8: Опыт волонтёрства
    elif step == "answer_8":
        user_data[user_id]["answer_8"] = message.text
        user_data[user_id]["step"] = "answer_9"
        await message.answer(
            "9/9. Nega aynan sizni volontyorlikka olishimiz kerak?\n\n"
            "(Bitta xabarda yozing 📝)"
        )

    # ШАГ 9: Почему именно вы
    elif step == "answer_9":
        user_data[user_id]["answer_9"] = message.text
        user_data[user_id]["step"] = "completed"
        await message.answer(
            "Ma'lumotlaringiz qabul qilindi. Tez orada xabarni beramiz! ✅"
        )


@dp.message(F.video | F.video_note)
async def get_video(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_data or user_data[user_id].get("step") != "video":
        return

    if message.video:
        user_data[user_id]["video"] = message.video.file_id
    elif message.video_note:
        user_data[user_id]["video"] = message.video_note.file_id

    user_data[user_id]["step"] = "answer_7"
    await message.answer(
        "7/9. Hozir qayerda o'qiysiz yoki ishlaysiz?\n\n(Bitta xabarda yozing)"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())