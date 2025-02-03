# Импорт необходимых библиотек
import pygame
import random
import sqlite3

# Инициализация Pygame
pygame.init()

# Определение констант для размеров экрана, размера блока и цветов
screen_width = 600  # Ширина экрана
screen_height = 800  # Высота экрана
block_size = 30  # Размер одного блока
black = (0, 0, 0)  # Черный цвет
white = (255, 255, 255)  # Белый цвет
red = (255, 0, 0)  # Красный цвет
background_color = (51, 51, 153)  # Цвет фона
selection_area_color = (50, 50, 50)  # Цвет области выбора блоков
block_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]  # Цвета блоков
screen = pygame.display.set_mode((screen_width, screen_height))  # Создание окна игры

# Определение форм блоков
block_shapes = [
    [[1, 1],
     [1, 1]],  # Квадрат 2x2
    [[1, 0, 0],
     [1, 1, 1]],  # L-образная форма
    [[0, 0, 1],
     [1, 1, 1]],  # Обратная L-образная форма
    [[0, 1, 0],
     [1, 1, 1]],  # T-образная форма
    [[1, 1, 1, 1]],  # Прямая линия
    [[1, 1],
     [0, 1],
     [0, 1]]  # Z-образная форма
]

# Функция для затемнения цвета
def darken_color(color, factor=0.7):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))

# Класс для представления блока
class Block:
    def __init__(self, x, y, shape, color):
        self.x = x  # Позиция блока по оси X
        self.y = y  # Позиция блока по оси Y
        self.shape = shape  # Форма блока
        self.color = color  # Цвет блока
        self.blocks = []  # Список прямоугольников, представляющих блок
        for row_index, row in enumerate(self.shape):
            for col_index, cell in enumerate(row):
                if cell:
                    # Создание прямоугольника для каждой ячейки блока
                    block_rect = pygame.Rect(x + col_index * block_size, y + row_index * block_size, block_size, block_size)
                    self.blocks.append(block_rect)

    # Метод для перемещения блока
    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        for block_rect in self.blocks:
            block_rect.move_ip(dx, dy)

    # Метод для отрисовки тени блока
    def draw_shadow(self, surface):
        shadow_color = darken_color(self.color)
        for block_rect in self.blocks:
            shadow_rect = block_rect.move(3, 3)
            pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=3)

    # Метод для отрисовки блока
    def draw(self, surface):
        self.draw_shadow(surface)
        for block_rect in self.blocks:
            pygame.draw.rect(surface, self.color, block_rect, border_radius=3)

# Функция для отрисовки текста на экране
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

# Функция для проверки столкновений блока с другими блоками или границами поля
def check_collision(block, placed_blocks, playing_field):
    for block_rect in block.blocks:
        if block_rect.y + block_size > playing_field.bottom:
            return True
        for placed_block in placed_blocks:
            for placed_block_rect in placed_block.blocks:
                if block_rect.colliderect(placed_block_rect):
                    return True
    return False

# Функция для удаления заполненных строк и столбцов
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
    full_rows = [row for row, count in rows.items() if count == 10]
    full_columns = [col for col, count in columns.items() if count == 16]

    score_gained = 0

    if full_rows or full_columns:
        new_blocks = []
        for block in placed_blocks:
            is_block_part_of_full = False
            for block_rect in block.blocks:
                if (block_rect.y - playing_field.y) // block_size in full_rows or (block_rect.x - playing_field.x) // block_size in full_columns:
                    is_block_part_of_full = True
                    break
            if not is_block_part_of_full:
                new_blocks.append(block)
        placed_blocks = new_blocks

        for block in placed_blocks:
            for block_rect in block.blocks:
                y_position = (block_rect.y - playing_field.y) // block_size
                shift_y = 0
                for row_to_remove in full_rows:
                    if y_position < row_to_remove:
                        shift_y += len(full_rows)
                block.move(0, shift_y * block_size)

        score_gained = len(full_rows) * 100 + len(full_columns) * 100
        return score_gained, placed_blocks
    else:
        return 0, placed_blocks

# Функция для анимации очистки строк (пока не реализована)
def animate_row_clear():
    pass

# Функция для регистрации пользователя
def run_registration():
    username = ""
    input_rect = pygame.Rect(screen_width // 2 - 150, screen_height // 2 - 25, 300, 50)
    active = True
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_rect.collidepoint(event.pos):
                    active = True
                else:
                    active = False
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        if username:
                            return "menu"
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    else:
                        username += event.unicode
        screen.fill(black)
        pygame.draw.rect(screen, white, input_rect, 2)
        font = pygame.font.Font(None, 36)
        text_surface = font.render(username, True, white)
        screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))
        draw_text("Enter your username:", 32, white, screen_width // 2, screen_height // 2 - 75)
        pygame.display.flip()

# Функция для отображения главного меню
def run_menu():
    button_width = 200
    button_height = 50
    button_x = screen_width // 2 - button_width // 2
    play_button_y = screen_height // 2 - button_height // 2 - 70
    settings_button_y = screen_height // 2 - button_height // 2
    exit_button_y = screen_height // 2 - button_height // 2 + 70
    font = pygame.font.Font(None, 36)
    play_button_text = font.render("Play", True, black)
    settings_button_text = font.render("Settings", True, black)
    exit_button_text = font.render("Exit", True, black)
    play_button_rect = pygame.Rect(button_x, play_button_y, button_width, button_height)
    settings_button_rect = pygame.Rect(button_x, settings_button_y, button_width, button_height)
    exit_button_rect = pygame.Rect(button_x, exit_button_y, button_width, button_height)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if play_button_rect.collidepoint(mouse_x, mouse_y):
                    return "game"
                if settings_button_rect.collidepoint(mouse_x, mouse_y):
                    return "settings"
                if exit_button_rect.collidepoint(mouse_x, mouse_y):
                    return "quit"
        screen.fill(white)
        draw_text("Block Blast", 64, black, screen_width // 2, screen_height // 2 - 150)
        pygame.draw.rect(screen, (200, 200, 200), play_button_rect)
        screen.blit(play_button_text, (play_button_rect.x + button_width // 2 - play_button_text.get_width() // 2,
                                       play_button_rect.y + button_height // 2 - play_button_text.get_height() // 2))
        pygame.draw.rect(screen, (200, 200, 200), settings_button_rect)
        screen.blit(settings_button_text, (settings_button_rect.x + button_width // 2 - settings_button_text.get_width() // 2,
                                      settings_button_rect.y + button_height // 2 - settings_button_text.get_height() // 2))
        pygame.draw.rect(screen, (200, 200, 200), exit_button_rect)
        screen.blit(exit_button_text, (exit_button_rect.x + button_width // 2 - exit_button_text.get_width() // 2,
                                      exit_button_rect.y + button_height // 2 - exit_button_text.get_height() // 2))
        pygame.display.flip()

# Функция для отображения настроек
def run_settings():
    button_width = 200
    button_height = 50
    button_x = screen_width // 2 - button_width // 2
    colors_button_y = screen_height // 2 - button_height // 2 - 70
    back_button_y = screen_height // 2 - button_height // 2 + 70
    font = pygame.font.Font(None, 36)
    colors_button_text = font.render("Colors", True, black)
    back_button_text = font.render("Back", True, black)
    colors_button_rect = pygame.Rect(button_x, colors_button_y, button_width, button_height)
    back_button_rect = pygame.Rect(button_x, back_button_y, button_width, button_height)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if colors_button_rect.collidepoint(mouse_x, mouse_y):
                    return "colors"
                if back_button_rect.collidepoint(mouse_x, mouse_y):
                    return "menu"
        screen.fill(white)
        draw_text("Settings", 64, black, screen_width // 2, screen_height // 2 - 150)
        pygame.draw.rect(screen, (200, 200, 200), colors_button_rect)
        screen.blit(colors_button_text, (colors_button_rect.x + button_width // 2 - colors_button_text.get_width() // 2,
                                       colors_button_rect.y + button_height // 2 - colors_button_text.get_height() // 2))
        pygame.draw.rect(screen, (200, 200, 200), back_button_rect)
        screen.blit(back_button_text, (back_button_rect.x + button_width // 2 - back_button_text.get_width() // 2,
                                      back_button_rect.y + button_height // 2 - back_button_text.get_height() // 2))
        pygame.display.flip()

# Функция для запуска игры
def run_game():
    global score, game_over, blocks, drop_interval, level, fall_speed
    score = 0  # Счет игры
    game_over = False  # Флаг окончания игры
    level = 1  # Уровень игры
    drop_interval = 1000  # Интервал падения блоков
    fall_speed = 2  # Скорость падения блоков
    blocks = []  # Список блоков
    placed_blocks = []  # Список размещенных блоков

    # Определение игрового поля и области выбора блоков
    playing_field = pygame.Rect(screen_width // 2 - (block_size * 10) // 2, 100, block_size * 10, block_size * 16)
    selection_area = pygame.Rect(0, screen_height - block_size * 4, screen_width, block_size * 4)
    block_selection = []

    # Создание блоков для выбора
    for i in range(3):
        cell_width = selection_area.width // 3
        x = selection_area.x + cell_width * i + (cell_width - block_size * 3) // 2
        y = selection_area.y + (selection_area.height - block_size * 3) // 2

        shape = random.choice(block_shapes)
        color = random.choice(block_colors)
        block_selection.append(Block(x, y, shape, color))

    selected_block = None  # Выбранный блок
    dragging = False  # Флаг перетаскивания блока
    offset_x = 0  # Смещение по оси X при перетаскивании
    offset_y = 0  # Смещение по оси Y при перетаскивании

    game_clock = pygame.time.Clock()  # Таймер для управления частотой кадров
    while True:
        time_delta = game_clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "menu"
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                for index, block in enumerate(block_selection):
                    for block_rect in block.blocks:
                        if block_rect.collidepoint(mouse_x, mouse_y):
                            selected_block = block
                            block_selection.pop(index)
                            cell_width = selection_area.width // 3
                            x = selection_area.x + cell_width * index + (cell_width - block_size * 3) // 2
                            y = selection_area.y + (selection_area.height - block_size * 3) // 2
                            shape = random.choice(block_shapes)
                            color = random.choice(block_colors)
                            block_selection.insert(index, Block(x, y, shape, color))
                            dragging = True
                            offset_x = mouse_x - selected_block.x
                            offset_y = mouse_y - selected_block.y
                            break
                    else:
                        continue
                    break
            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging and selected_block:
                    dragging = False
                    grid_x = round((selected_block.x - playing_field.x) / block_size) * block_size + playing_field.x
                    grid_y = round((selected_block.y - playing_field.y) / block_size) * block_size + playing_field.y
                    selected_block.move(grid_x - selected_block.x, grid_y - selected_block.y)
                    if not check_collision(selected_block, placed_blocks, playing_field):
                        placed_blocks.append(selected_block)
                        selected_block = None
                    else:
                        selected_block = None

            elif event.type == pygame.MOUSEMOTION:
                if dragging and selected_block:
                    mouse_x, mouse_y = event.pos
                    selected_block.move(mouse_x - selected_block.x - offset_x, mouse_y - selected_block.y - offset_y)

        if not game_over:
            screen.fill(background_color)

            for i in range(screen_height // block_size):
                pygame.draw.line(screen, (20, 20, 70), (0, i * block_size), (screen_width, i * block_size), 1)
            for i in range(screen_width // block_size):
                pygame.draw.line(screen, (20, 20, 70), (i * block_size, 0), (i * block_size, screen_height), 1)

            pygame.draw.rect(screen, selection_area_color, selection_area)

            pygame.draw.rect(screen, (30, 30, 80), playing_field, border_radius=5)
            for block in placed_blocks:
                block.draw(screen)
            for block in block_selection:
                block.draw(screen)
            if selected_block:
                selected_block.draw(screen)
            score_from_clearing, placed_blocks = remove_full_rows_and_columns(placed_blocks, playing_field)
            animate_row_clear()
            score += score_from_clearing
            draw_score()
            # draw_level() # Убрали вызов функции draw_level
            pygame.display.flip()
            if score >= level * 1000:
                level += 1
                drop_interval = max(200, drop_interval - 100)
                fall_speed = min(10, fall_speed + 1)
        else:
            screen.fill(black)
            draw_text(f"Game Over!", 64, red, screen_width // 2, screen_height // 2 - 50)
            draw_text(f"Final Score: {score}", 32, white, screen_width // 2, screen_height // 2 + 50)
            pygame.display.flip()
        if game_over:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    return "menu"


current_screen = "registration"
while True:
    if current_screen == "registration":
        current_screen = run_registration()
    elif current_screen == "menu":
        current_screen = run_menu()
    elif current_screen == "settings":
        current_screen = run_settings()
    elif current_screen == "game":
        current_screen = run_game()
    elif current_screen == "quit":
        break
pygame.quit()
