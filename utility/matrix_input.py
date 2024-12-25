from tabulate import tabulate
import os
import sys
import tty
import termios
from typing import Union, Callable, Optional, Tuple

def getch():
    """Get a single character from stdin."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def format_number(value: str, as_int: bool = False, as_symbol: bool = False) -> str:
    """Format number string by removing leading zeros and proper decimal handling."""
    if as_symbol:
        return value
    try:
        if as_int:
            return str(int(float(value)))
        else:
            num = float(value)
            # Remove trailing zeros after decimal point
            s = f"{num}"
            if '.' in s:
                s = s.rstrip('0').rstrip('.')
            return s
    except ValueError:
        return value

def input_matrix(rows: int, cols: int, as_int: bool = False, as_symbol: bool = False,
                validator: Optional[Callable[[str], Tuple[bool, str]]] = None) -> list[list]:
    """
    Интерактивный ввод матрицы с форматированной сеткой.
    Ввод осуществляется посимвольно прямо в сетке.
    
    Args:
        rows (int): Количество строк матрицы
        cols (int): Количество столбцов матрицы
        as_int (bool): Если True, все значения будут преобразованы в целые числа
        as_symbol (bool): Если True, значения будут восприниматься как символы
        validator (callable, optional): Функция для проверки вводимых значений.
                                     Должна возвращать кортеж (bool, str) - (корректно, сообщение_об_ошибке)
                                     Если None, принимаются любые числовые значения или символы
    
    Returns:
        list[list]: Введенная матрица
    """
    def default_validator(value: str) -> Tuple[bool, str]:
        if as_symbol:
            if len(value) == 1:
                return True, ""
            return False, "Введите один символ"
        try:
            if as_int:
                int(float(value))  # Check if can be converted to int
            else:
                float(value)
            return True, ""
        except ValueError:
            return False, "Введите корректное число"
    
    if validator is None:
        validator = default_validator
    
    matrix = [['' for _ in range(cols)] for _ in range(rows)]
    current_row, current_col = 0, 0
    current_value = ''
    error_message = ''
    last_display_lines = 0
    first_display = True
    
    def move_cursor_up(n):
        if n > 0:
            print(f"\033[{n}A", end='')
    
    def clear_line():
        print("\033[2K", end='')
    
    def is_matrix_complete():
        return all(all(cell != '' for cell in row) for row in matrix)
    
    def find_next_empty(row: int, col: int):
        """Find the next empty cell after the current position."""
        # Continue from current position
        next_col = col + 1
        for i in range(row, rows):
            # If we're continuing from middle of row
            start_col = next_col if i == row else 0
            for j in range(start_col, cols):
                if matrix[i][j] == '':
                    return i, j
        return None

    def find_prev_empty(row: int, col: int):
        """Find the first empty cell from the start up to current position."""
        # Check all cells from start up to current position
        for i in range(row + 1):
            for j in range(cols):
                # Skip if we're at or after current position in the last row
                if i == row and j >= col:
                    break
                if matrix[i][j] == '':
                    return i, j
        return None

    def display_matrix():
        nonlocal last_display_lines, first_display
        
        # Generate table content
        headers = [f"Ст. {i+1}" for i in range(cols)]
        table = []
        for i in range(rows):
            row = [f"Стр. {i+1}"]
            for j in range(cols):
                if i == current_row and j == current_col:
                    value = current_value + '█' if current_value else '█'
                    row.append(value)
                else:
                    value = matrix[i][j]
                    row.append(value)
            table.append(row)
        
        # Generate all display content first
        table_str = tabulate(table, headers=[''] + headers, tablefmt='rounded_grid', stralign='right')
        display_lines = table_str.split('\n')
        display_lines.append("ESC - отмена, Enter - ввод, ← → ↑ ↓ - перемещение")
        
        if error_message:
            display_lines.append(f"Ошибка: {error_message}")
        
        if not first_display:
            # Clear previous display
            move_cursor_up(last_display_lines)
            for _ in range(last_display_lines):
                clear_line()
                print()
            move_cursor_up(last_display_lines)
        
        # Print new display
        print('\n'.join(display_lines))
        
        # Update line count for next refresh
        last_display_lines = len(display_lines)
        first_display = False
    
    while True:
        display_matrix()
        
        char = getch()
        
        # Handle special keys
        if ord(char) == 27:  # Esc
            next_char = getch()
            if next_char == '[':  # Arrow keys
                direction = getch()
                if direction == 'A' and current_row > 0:  # Up
                    current_row -= 1
                    current_value = ''
                    error_message = ''
                elif direction == 'B' and current_row < rows - 1:  # Down
                    current_row += 1
                    current_value = ''
                    error_message = ''
                elif direction == 'D' and current_col > 0:  # Left
                    current_col -= 1
                    current_value = ''
                    error_message = ''
                elif direction == 'C' and current_col < cols - 1:  # Right
                    current_col += 1
                    current_value = ''
                    error_message = ''
                continue
            print()  # Move to next line before returning
            return None
        elif ord(char) == 13:  # Enter
            if current_value:
                # Only try to format and validate if there's any input
                try:
                    # First check if the input format is valid
                    if as_int:
                        test_value = int(float(current_value))
                    elif as_symbol:
                        test_value = current_value
                    else:
                        test_value = float(current_value)
                    
                    # Then run it through the validator
                    is_valid, error = validator(current_value)
                    if is_valid:
                        formatted_value = format_number(current_value, as_int, as_symbol)
                        matrix[current_row][current_col] = formatted_value
                        current_value = ''
                        error_message = ''
                        
                        # First try to find next empty cell
                        next_empty = find_next_empty(current_row, current_col)
                        if next_empty is not None:
                            current_row, current_col = next_empty
                        else:
                            # If no next empty, try to find previous empty
                            prev_empty = find_prev_empty(current_row, current_col)
                            if prev_empty is not None:
                                current_row, current_col = prev_empty
                            else:
                                # No empty cells left, return matrix
                                print()  # Move to next line before returning
                                return matrix
                    else:
                        error_message = error
                except ValueError:
                    error_message = "Введите корректное число"
            continue
        elif ord(char) == 127:  # Backspace
            if current_value:
                current_value = current_value[:-1]
                error_message = ''
            continue
        
        # Handle regular input - allow all printable characters but validate on Enter
        if char.isprintable():
            current_value += char
            error_message = ''

def input_float_matrix(rows: int, cols: int,
                    validator: Optional[Callable[[str], Tuple[bool, str]]] = None) -> list[list[float]]:
    """
    Интерактивный ввод матрицы вещественных чисел.
    
    Args:
        rows (int): Количество строк матрицы
        cols (int): Количество столбцов матрицы
        validator (callable, optional): Функция для проверки вводимых значений
        
    Returns:
        list[list[float]]: Введенная матрица вещественных чисел
    """
    matrix = input_matrix(rows, cols, as_int=False, validator=validator)
    return [[float(val) for val in row] for row in matrix]

def input_int_matrix(rows: int, cols: int,
                   validator: Optional[Callable[[str], Tuple[bool, str]]] = None) -> list[list[int]]:
    """
    Интерактивный ввод матрицы целых чисел.
    
    Args:
        rows (int): Количество строк матрицы
        cols (int): Количество столбцов матрицы
        validator (callable, optional): Функция для проверки вводимых значений
        
    Returns:
        list[list[int]]: Введенная матрица целых чисел
    """
    matrix = input_matrix(rows, cols, as_int=True, validator=validator)
    return [[int(float(val)) for val in row] for row in matrix]

def input_symbol_matrix(rows: int, cols: int,
                    validator: Optional[Callable[[str], Tuple[bool, str]]] = None) -> list[list[str]]:
    """
    Интерактивный ввод матрицы символов.
    
    Args:
        rows (int): Количество строк матрицы
        cols (int): Количество столбцов матрицы
        validator (callable, optional): Функция для проверки вводимых значений
        
    Returns:
        list[list[str]]: Введенная матрица символов
    """
    matrix = input_matrix(rows, cols, as_symbol=True, validator=validator)
    return matrix

# Example usage with custom validator
if __name__ == "__main__":
    def custom_validator(value: str) -> Tuple[bool, str]:
        try:
            num = float(value)
            if -100 <= num <= 100:
                return True, ""
            return False, "Число должно быть от -100 до 100"
        except ValueError:
            return False, "Введите корректное число"
    
    print("Ввод матрицы 3x3 (значения от -100 до 100):")
    
    # Example for integer input
    result = input_matrix(3, 3, as_int=False, validator=custom_validator)
    
    if result:
        print("\nИтоговая матрица:")
        headers = [f"Ст. {i+1}" for i in range(3)]
        table = [[f"Стр. {i+1}"] + row for i, row in enumerate(result)]
        print(tabulate(table, headers=[''] + headers, tablefmt='rounded_grid'))