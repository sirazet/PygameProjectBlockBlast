
import pygame
import random
import sqlite3
import os
import time

pygame.init()

# Размеры экрана и блоков
screen_width = 600
screen_height = 800
block_size = 30

# Цвета
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
background_color = (51, 51, 153)
selection_area_color = (50, 50, 50)
block_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

# Настройка экрана
screen = pygame.display.set_mode((screen_width, screen_height))

# Загрузка фона
background_image_path = "background.png"
background_image = None
try:
    if os.path.exists(background_image_path):
        background_image = pygame.image.load(background_image_path)
        background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
    else:
        print("Файл фона не найден. Игра будет работать без фона.")
except pygame.error as e:
    print(f"Ошибка при загрузке фона: {e}")

# Формы блоков
block_shapes = [
    [[1, 1],
     [1, 1]],
    [[1, 0, 0],
     [1, 1, 1]],
    [[0, 0, 1],
     [1, 1, 1]],
    [[0, 1, 0],
     [1, 1, 1]],
    [[1, 1, 1, 1]],
    [[1, 1],
     [0, 1],
     [0, 1]]
]

# Функция для затемнения цвета
def darken_color(color, factor=0.7):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))

# Класс для представления блока
class Block:
    def __init__(self, x, y, shape, color):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = color
        self.blocks = []
        for row_index, row in enumerate(self.shape):
            for col_index, cell in enumerate(row):
                if cell:
                    block_rect = pygame.Rect(x + col_index * block_size, y + row_index * block_size, block_size,
                                           block_size)
                    self.blocks.append(block_rect)

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        for block_rect in self.blocks:
            block_rect.move_ip(dx, dy)

    def draw_shadow(self, surface):
        shadow_color = darken_color(self.color)
        for block_rect in self.blocks:
            shadow_rect = block_rect.move(3,3)
            pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=3)

    def draw(self, surface):
        self.draw_shadow(surface)
        for block_rect in self.blocks:
            pygame.draw.rect(surface, self.color, block_rect, border_radius=3)

# Функция для отрисовки текста
def draw_text(text, size, color, x, y):
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

# Функция для отрисовки счета
def draw_score():
    global score
    draw_text(f"{score}", 32, white, 40, 30)

# Функция для отрисовки уровня
def draw_level():
    global level
    draw_text(f"{level}", 32, white, screen_width - 40, 30)

# Функция для проверки столкновения
def check_collision(block, placed_blocks, playing_field):
    for block_rect in block.blocks:
        # Проверяем столкновение только с нижней границей и другими блоками
        if block_rect.y + block_size > playing_field.bottom:
            return True
        for placed_block in placed_blocks:
            for placed_block_rect in placed_block.blocks:
                if block_rect.colliderect(placed_block_rect):
                    return True
        if block_rect.x < playing_field.x or block_rect.x + block_size > playing_field.right:
            return True # Столкновение с боковыми границами
    return False

# Функция для удаления полных строк и столбцов
def remove_full_rows_and_columns(placed_blocks, playing_field):
    rows = {}
    columns = {}
    for block in placed_blocks:
        for block_rect in block.blocks:
            row_num = (block_rect.y - playing_field.y) // block_size
            col_num = (block_rect.x - playing_field.x) // block_size
            if row_num not in rows:
                rows[row_num] = 0
            if col_num not in columns:
                columns[col_num] = 0
            rows[row_num] += 1
            columns[col_num] += 1
    full_rows = [row for row, count in rows.items() if count == 10]  # Строка полна, если в ней 10 блоков
    full_columns = [col for col, count in columns.items() if count == 16] # Столбец полон, если в нем 16 блоков

    score_gained = 0
    if full_rows or full_columns:
        score_gained = len(full_rows) * 100 + len(full_columns) * 100
        return score_gained, placed_blocks, full_rows, full_columns
    else:
        return 0, placed_blocks, [], []

# Анимация очистки строки
def animate_row_clear(placed_blocks, full_rows, full_columns, playing_field):
    
    flash_color = (255,255,255) # Белый цвет для анимации исчезновения


    for row_to_remove in full_rows:
      for block in placed_blocks:
        for block_rect in block.blocks:
            y_position = (block_rect.y - playing_field.y) // block_size
            if y_position == row_to_remove:
                pygame.draw.rect(screen, flash_color, block_rect, border_radius=3) # Рисуем поверх блока белым цветом

    for col_to_remove in full_columns:
      for block in placed_blocks:
        for block_rect in block.blocks:
            x_position = (block_rect.x - playing_field.x) // block_size
            if x_position == col_to_remove:
                pygame.draw.rect(screen, flash_color, block_rect, border_radius=3) # Рисуем поверх блока белым цветом

    pygame.display.flip() # Обновляем экран
    time.sleep(0.1) # Небольшая задержка

    # Создаем новый список блоков, исключая полные строки/столбцы
    new_blocks = []
    for block in placed_blocks:
        is_block_part_of_full = False
        for block_rect in block.blocks:
            if (block_rect.y - playing_field.y) // block_size in full_rows or (block_rect.x - playing_field.x) // block_size in full_columns:
                is_block_part_of_full = True
                break
        if not is_block_part_of_full:
            new_blocks.append(block) # Добавляем блок, если он не часть полной строки/столбца
    placed_blocks = new_blocks # Обновляем список блоков

    # Сдвигаем блоки, находящиеся выше удаленных строк, вниз
    for block in placed_blocks:
          for block_rect in block.blocks:
              y_position = (block_rect.y - playing_field.y) // block_size
              shift_y = 0
              for row_to_remove in full_rows:
                  if y_position < row_to_remove:
                      shift_y += len(full_rows) # На сколько строк сдвинуть блок
              block.move(0, shift_y * block_size) # Сдвигаем блок
    return placed_blocks

# Функция для экрана регистрации
def run_registration():
    username = ""  # Имя пользователя
    input_rect = pygame.Rect(screen_width // 2 - 150, screen_height // 2 - 25, 300, 50) # Прямоугольник для ввода имени
    active = True  # Активен ли ввод имени
    error_message = "" # Сообщение об ошибке

    # Подключение к базе данных
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()

    try:
        # Создание таблицы пользователей, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                high_score INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при создании таблицы: {e}")
        conn.close()
        return "menu", None

    # Создание кнопок
    continue_button_width = 200
    continue_button_height = 50
    continue_button_x = screen_width // 2 - continue_button_width // 2
    continue_button_y = screen_height // 2 + 50
    continue_button_rect = pygame.Rect(continue_button_x, continue_button_y, continue_button_width, continue_button_height)
    font = pygame.font.Font(None, 36)
    continue_button_text = font.render("Continue", True, black)

    delete_button_width = 150
    delete_button_height = 30
    delete_button_x = screen_width // 2 - delete_button_width // 2
    delete_button_y = screen_height // 2 + 120
    delete_button_rect = pygame.Rect(delete_button_x, delete_button_y, delete_button_width, delete_button_height)
    delete_button_text = font.render("Delete Users", True, black)

    # Основной цикл экрана регистрации
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                conn.close()
                return "quit", None
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Обработка нажатия на поле ввода имени
                if input_rect.collidepoint(event.pos):
                    active = True
                    error_message = ""
                # Обработка нажатия на кнопку "Continue"
                elif continue_button_rect.collidepoint(event.pos):
                    if username:
                        try:
                            # Проверка, существует ли пользователь с таким именем
                            cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                            existing_user = cursor.fetchone()
                            if existing_user:
                                error_message = "Username already exists!"
                            else:
                                # Добавление нового пользователя
                                cursor.execute("INSERT INTO users (username, high_score) VALUES (?, ?)", (username, 0))
                                conn.commit()
                                conn.close()
                                return "menu", username
                        except sqlite3.Error as e:
                             print(f"Ошибка при сохранении пользователя: {e}")
                             conn.close()
                             return "menu", None
                # Обработка нажатия на кнопку "Delete Users"
                elif delete_button_rect.collidepoint(event.pos):
                    try:
                        # Удаление всех пользователей из базы данных
                        cursor.execute("DELETE FROM users")
                        conn.commit()
                    except sqlite3.Error as e:
                        print(f"Ошибка при удалении пользователей: {e}")
                    conn.close()
                    return "registration", None
                else:
                    active = False # Снимаем фокус с поля ввода
            if event.type == pygame.KEYDOWN:
                if active:
                    # Обработка нажатия Enter
                    if event.key == pygame.K_RETURN:
                        if username:
                            try:
                                # Проверка, существует ли пользователь с таким именем
                                cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                                existing_user = cursor.fetchone()
                                if existing_user:
                                   error_message = "Username already exists!"
                                else:
                                    # Добавление нового пользователя
                                    cursor.execute("INSERT INTO users (username, high_score) VALUES (?, ?)", (username, 0))
                                    conn.commit()
                                    conn.close()
                                    return "menu", username
                            except sqlite3.Error as e:
                                print(f"Ошибка при сохранении пользователя: {e}")
                                conn.close()
                                return "menu", None
                    # Обработка Backspace
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    # Ввод символов
                    else:
                        username += event.unicode
        # Отрисовка элементов экрана
        screen.fill(black)
        pygame.draw.rect(screen, white, input_rect, 2)
        font = pygame.font.Font(None, 36)
        text_surface = font.render(username, True, white)
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))
        draw_text("Enter your username:", 32, white, screen_width // 2, screen_height // 2 - 75)

        pygame.draw.rect(screen, (200, 200, 200), continue_button_rect)
        screen.blit(continue_button_text, (continue_button_rect.x + continue_button_width // 2 - continue_button_text.get_width() // 2,
                                        continue_button_rect.y + continue_button_height // 2 - continue_button_text.get_height() // 2))

        pygame.draw.rect(screen, (200, 200, 200), delete_button_rect)
        screen.blit(delete_button_text, (delete_button_rect.x + delete_button_width // 2 - delete_button_text.get_width() // 2,
                                         delete_button_rect.y + delete_button_height // 2 - delete_button_text.get_height() // 2))

        if error_message:
            draw_text(error_message, 24, red, screen_width // 2, screen_height // 2 + 100)

        pygame.display.flip()

# Функция для экрана меню
def run_menu(username):
    button_width = 200
    button_height = 50
    button_x = screen_width // 2 - button_width // 2
    play_button_y = screen_height // 2 - button_height // 2 - 100
    database_button_y = screen_height // 2 - button_height // 2
    exit_button_y = screen_height // 2 - button_height // 2 + 100
    font = pygame.font.Font(None, 36)
    play_button_text = font.render("Play", True, black)
    database_button_text = font.render("Database", True, black)
    exit_button_text = font.render("Exit", True, black)
    play_button_rect = pygame.Rect(button_x, play_button_y, button_width, button_height)
    database_button_rect = pygame.Rect(button_x, database_button_y, button_width, button_height)
    exit_button_rect = pygame.Rect(button_x, exit_button_y, button_width, button_height)
    # Основной цикл экрана меню
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", None
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                # Переход в игру
                if play_button_rect.collidepoint(mouse_x, mouse_y):
                    return "game", username
                # Переход в базу данных
                if database_button_rect.collidepoint(mouse_x, mouse_y):
                    return "database", username
                # Выход из игры
                if exit_button_rect.collidepoint(mouse_x, mouse_y):
                    return "quit", None
        # Отрисовка элементов экрана
        screen.fill(white)
        draw_text("Block Blast", 64, black, screen_width // 2, screen_height // 2 - 200)
        pygame.draw.rect(screen, (200, 200, 200), play_button_rect)
        screen.blit(play_button_text, (play_button_rect.x + button_width // 2 - play_button_text.get_width() // 2,
                                       play_button_rect.y + button_height // 2 - play_button_text.get_height() // 2))
        pygame.draw.rect(screen, (200, 200, 200), database_button_rect)
        screen.blit(database_button_text, (database_button_rect.x + button_width // 2 - database_button_text.get_width() // 2,
                                       database_button_rect.y + button_height // 2 - database_button_text.get_height() // 2))
        pygame.draw.rect(screen, (200, 200, 200), exit_button_rect)
        screen.blit(exit_button_text, (exit_button_rect.x + button_width // 2 - exit_button_text.get_width() // 2,
                                      exit_button_rect.y + button_height // 2 - exit_button_text.get_height() // 2))
        pygame.display.flip()

# Функция для экрана базы данных
def run_database(username):
    # Подключение к базе данных
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()

    try:
        # Получение рекордов пользователей
        cursor.execute("SELECT username, high_score FROM users ORDER BY high_score DESC")
        scores = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Ошибка при чтении рекордов: {e}")
        scores = []
    conn.close()

    # Создание кнопки "Back"
    back_button_width = 100
    back_button_height = 30
    back_button_x = screen_width // 2 - back_button_width // 2
    back_button_y = screen_height - 100
    back_button_rect = pygame.Rect(back_button_x, back_button_y, back_button_width, back_button_height)
    font = pygame.font.Font(None, 32)
    back_button_text = font.render("Back", True, black)

    # Основной цикл экрана базы данных
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", None
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Переход в меню
                if back_button_rect.collidepoint(event.pos):
                    return "menu", username
        # Отрисовка элементов экрана
        screen.fill(white)
        draw_text("Database", 64, black, screen_width // 2, 100)

        y_offset = 200
        # Вывод рекордов
        if scores:
            for user, high_score in scores:
                draw_text(f"{user}: {high_score}", 32, black, screen_width // 2, y_offset)
                y_offset += 40
        else:
           draw_text("No high scores yet!", 32, black, screen_width // 2, y_offset)

        pygame.draw.rect(screen, (200, 200, 200), back_button_rect)
        screen.blit(back_button_text, (back_button_rect.x + back_button_width // 2 - back_button_text.get_width() // 2,
                                      back_button_rect.y + back_button_height // 2 - back_button_text.get_height() // 2))

        pygame.display.flip()

# Функция для экрана Game Over
def run_game_over(username, score):
    # Подключение к базе данных
    conn = sqlite3.connect('game_data.db')
    cursor = conn.cursor()
    updated = False

    try:
        # Получение личного рекорда пользователя
        cursor.execute("SELECT high_score FROM users WHERE username = ?", (username,))
        high_score_data = cursor.fetchone()
        high_score = high_score_data[0] if high_score_data else 0

        # Обновляем рекорд, если текущий счет больше
        if score > high_score:
            cursor.execute("UPDATE users SET high_score = ? WHERE username = ?", (score, username))
            conn.commit()
            high_score = score # Обновляем локальное значение high_score
            updated = True # Флаг, что рекорд был обновлен
    except sqlite3.Error as e:
        print(f"Ошибка при чтении/записи рекорда в run_game_over: {e}")
        high_score = 0
    finally:
        conn.close()

    # Основной цикл экрана Game Over
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", None
            # Возврат в меню по нажатию любой клавиши или кнопки мыши
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                 return "menu", username

        # Отрисовка элементов экрана
        screen.fill(black)
        draw_text(f"Game Over!", 64, red, screen_width // 2, screen_height // 2 - 100)
        draw_text(f"Final Score: {score}", 32, white, screen_width // 2, screen_height // 2)
        if updated:
            draw_text(f"New high score: {high_score}!", 32, white, screen_width // 2, screen_height // 2 + 50)
        else:
            draw_text(f"Your high score: {high_score}", 32, white, screen_width // 2, screen_height // 2 + 50)
        pygame.display.flip()

# Функция для игрового экрана
def run_game(username):
    global score, game_over, blocks, drop_interval, level, fall_speed
    score = 0  # Обнуляем счет
    game_over = False # Игра не окончена
    level = 1  # Начальный уровень
    drop_interval = 1000 # Интервал падения блоков (в миллисекундах)
    fall_speed = 2 # Скорость падения блоков
    blocks = [] # Список падающих блоков (не используется в этой версии)
    placed_blocks = [] # Список установленных блоков

    # Определяем границы игрового поля и области выбора блоков
    playing_field = pygame.Rect(screen_width // 2 - (block_size * 10) // 2, 100, block_size * 10, block_size * 16)
    selection_area = pygame.Rect(0, screen_height - block_size * 4, screen_width, block_size * 4)
    block_selection = [] # Список блоков для выбора

    # Создаем блоки для выбора
    for i in range(3):
        cell_width = selection_area.width // 3
        x = selection_area.x + cell_width * i + (cell_width - block_size * 3) // 2
        y = selection_area.y + (selection_area.height - block_size * 3) // 2 - 50  # Уменьшаем смещение

        shape = random.choice(block_shapes)
        color = random.choice(block_colors)
        block_selection.append(Block(x, y, shape, color))

    selected_block = None  # Выбранный блок
    dragging = False # Блок перетаскивается
    offset_x = 0 # Смещение по X при перетаскивании
    offset_y = 0 # Смещение по Y при перетаскивании
    
    # Новая логика проверки Game Over
    def check_game_over(placed_blocks, playing_field):
      # Проверяем, есть ли блоки, выходящие за верхнюю границу игрового поля
      for block in placed_blocks:
          for block_rect in block.blocks:
              if block_rect.top <= playing_field.top:
                  return True
      return False

    game_clock = pygame.time.Clock()
    # Основной цикл игрового экрана
    while True:
        time_delta = game_clock.tick(60) # Ограничиваем FPS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                 return "menu", username
            # Обработка нажатия кнопки мыши
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                # Проверяем, на какой блок из области выбора нажали
                for index, block in enumerate(block_selection):
                    for block_rect in block.blocks:
                        if block_rect.collidepoint(mouse_x, mouse_y):
                            selected_block = block # Выбираем блок
                            block_selection.pop(index) # Удаляем блок из области выбора
                            # Создаем новый блок в области выбора
                            cell_width = selection_area.width // 3
                            x = selection_area.x + cell_width * index + (cell_width - block_size * 3) // 2
                            y = selection_area.y + (selection_area.height - block_size * 3) // 2 - 50
                            shape = random.choice(block_shapes)
                            color = random.choice(block_colors)
                            block_selection.insert(index,Block(x,y,shape,color))
                            dragging = True # Начали перетаскивание
                            offset_x = mouse_x - selected_block.x # Смещение курсора относительно блока
                            offset_y = mouse_y - selected_block.y # Смещение курсора относительно блока
                            break # Прерываем поиск блока
                    else:
                        continue
                    break
            # Обработка отпускания кнопки мыши
            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging and selected_block:
                    dragging = False # Закончили перетаскивание
                    # Вычисляем позицию блока на игровом поле по сетке
                    grid_x = round((selected_block.x - playing_field.x) / block_size) * block_size + playing_field.x
                    grid_y = round((selected_block.y - playing_field.y) / block_size) * block_size + playing_field.y
                    selected_block.move(grid_x - selected_block.x, grid_y - selected_block.y) # Перемещаем блок в сетку
                    # Проверяем столкновение
                    if not check_collision(selected_block, placed_blocks, playing_field):
                        placed_blocks.append(selected_block) # Добавляем блок на игровое поле
                        selected_block = None # Сбрасываем выбранный блок
                        # Проверяем, не закончилась ли игра после добавления блока
                        if check_game_over(placed_blocks, playing_field):
                            game_over = True
                    else:
                        selected_block = None # Сбрасываем выбранный блок, если есть столкновение

            # Обработка движения мыши при перетаскивании
            elif event.type == pygame.MOUSEMOTION:
                if dragging and selected_block:
                    mouse_x, mouse_y = event.pos
                    selected_block.move(mouse_x - selected_block.x - offset_x, mouse_y - selected_block.y - offset_y) # Перемещаем блок вслед за курсором

        # Игровой цикл
        if not game_over:
            # Отрисовка фона
            if background_image:
                screen.blit(background_image, (0,0))
            else:
              screen.fill(background_color)

            # Отрисовка сетки (опционально)
            for i in range(screen_height // block_size):
                  pygame.draw.line(screen, (20, 20, 70), (0, i * block_size),(screen_width, i*block_size),1)
            for i in range(screen_width // block_size):
                  pygame.draw.line(screen, (20, 20, 70), (i*block_size, 0), (i*block_size, screen_height), 1)

            # Отрисовка области выбора
            pygame.draw.rect(screen, selection_area_color, selection_area)

            # Отрисовка игрового поля
            pygame.draw.rect(screen, (30, 30, 80), playing_field, border_radius=5)

            # Отрисовка установленных блоков
            for block in placed_blocks:
                block.draw(screen)
            # Отрисовка блоков в области выбора
            for block in block_selection:
                block.draw(screen)
            # Отрисовка перетаскиваемого блока
            if selected_block:
                selected_block.draw(screen)

            # Проверка и удаление полных строк и столбцов
            score_from_clearing, placed_blocks, full_rows, full_columns = remove_full_rows_and_columns(placed_blocks, playing_field)
            score += score_from_clearing # Добавляем очки за удаленные строки/столбцы

            # Анимация очистки строк и столбцов
            if full_rows or full_columns:
                placed_blocks = animate_row_clear(placed_blocks, full_rows, full_columns, playing_field)

            # Проверка Game Over после очистки строк
            if check_game_over(placed_blocks, playing_field):
                game_over = True

            # Отрисовка счета и уровня
            draw_score()
            draw_level()

            # Обновляем экран
            pygame.display.flip()

            # Повышение уровня
            if score >= level * 1000:
                level += 1
                drop_interval = max(200, drop_interval - 100) # Увеличиваем скорость падения
                fall_speed = min(10, fall_speed + 1) # Увеличиваем скорость падения
        else:
            return "game_over", (username, score)


# Основной цикл игры
current_screen = "registration" # Начальный экран - регистрация
current_username = None # Имя текущего пользователя
current_score = 0 # Текущий счет

while True:
    # Переключение между экранами
    if current_screen == "registration":
        current_screen, current_username = run_registration()
    elif current_screen == "menu":
        current_screen, current_username = run_menu(current_username)
    elif current_screen == "database":
        current_screen, current_username = run_database(current_username)
    elif current_screen == "game":
        current_screen, (current_username, current_score) = run_game(current_username)
    elif current_screen == "game_over":
        current_screen, current_username = run_game_over(current_username, current_score)
    elif current_screen == "quit":
        break

pygame.quit() # Выход из Pygame
