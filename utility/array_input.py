from tabulate import tabulate
import os
import sys
import tty
import termios
from typing import Union, Callable, Optional, Tuple, List

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

def format_number(value: str, as_int: bool = False) -> str:
    """Format number string by removing leading zeros and proper decimal handling."""
    try:
        if as_int:
            return str(int(float(value)))
        else:
            num = float(value)
            s = f"{num}"
            if '.' in s:
                s = s.rstrip('0').rstrip('.')
            return s
    except ValueError:
        return value

def input_array(size: int, as_int: bool = False,
               validator: Optional[Callable[[str], Tuple[bool, str]]] = None) -> Optional[list]:
    """
    Интерактивный ввод массива с форматированной сеткой.
    Ввод осуществляется посимвольно прямо в сетке.
    
    Args:
        size (int): Размер массива
        as_int (bool): Если True, все значения будут преобразованы в целые числа
        validator (callable, optional): Функция для проверки вводимых значений.
                                     Должна возвращать кортеж (bool, str) - (корректно, сообщение_об_ошибке)
    
    Returns:
        Optional[list]: Введенный массив или None если ввод был отменен
    """
    def default_validator(value: str) -> Tuple[bool, str]:
        try:
            if as_int:
                int(float(value))
            else:
                float(value)
            return True, ""
        except ValueError:
            return False, "Введите корректное число"
    
    if validator is None:
        validator = default_validator
    
    array = [''] * size
    current_pos = 0
    current_value = ''
    error_message = ''
    last_display_lines = 0
    first_display = True
    
    def move_cursor_up(n):
        if n > 0:
            print(f"\033[{n}A", end='')
    
    def clear_line():
        print("\033[2K", end='')
    
    def display_array():
        nonlocal last_display_lines, first_display
        
        # Generate array display
        display = ['[']
        for i in range(size):
            if i == current_pos:
                value = current_value + '█' if current_value else '█'
            else:
                value = array[i] if array[i] != '' else '_'
            display.append(value)
            if i < size - 1:
                display.append(', ')
        display.append(']')
        
        # Convert to string
        display_str = ''.join(display)
        display_lines = [display_str]
        display_lines.append("ESC - отмена, Enter - ввод, ← → - перемещение")
        
        if error_message:
            display_lines.append(f"Ошибка: {error_message}")
        
        if not first_display:
            move_cursor_up(last_display_lines)
            for _ in range(last_display_lines):
                clear_line()
                print()
            move_cursor_up(last_display_lines)
        
        print('\n'.join(display_lines))
        last_display_lines = len(display_lines)
        first_display = False
    
    while True:
        display_array()
        
        char = getch()
        
        if char == '\r' or char == '\n':  # Enter
            if current_value:
                is_valid, error = validator(current_value)
                if is_valid:
                    array[current_pos] = format_number(current_value, as_int)
                    current_value = ''
                    if current_pos < size - 1:
                        current_pos += 1
                    error_message = ''
                else:
                    error_message = error
            elif current_pos < size - 1:
                current_pos += 1
        elif char == '\x7f':  # Backspace
            if current_value:
                current_value = current_value[:-1]
                error_message = ''
        elif char == '\x1b':  # Escape sequence
            next_char = getch()
            if next_char == '[':  # Arrow keys
                direction = getch()
                if direction == 'D' and current_pos > 0:  # Left
                    current_pos -= 1
                    current_value = ''
                    error_message = ''
                elif direction == 'C' and current_pos < size - 1:  # Right
                    current_pos += 1
                    current_value = ''
                    error_message = ''
            else:  # Just Escape - cancel input
                print()  # Move to next line before returning
                return None
        elif char.isprintable():
            current_value += char
            error_message = ''
        
        # Check if array is complete
        if all(cell != '' for cell in array):
            break
    
    return array

def input_float_array(size: int,
                   validator: Optional[Callable[[str], Tuple[bool, str]]] = None) -> Optional[List[float]]:
    """
    Интерактивный ввод массива вещественных чисел.
    
    Args:
        size (int): Размер массива
        validator (callable, optional): Функция для проверки вводимых значений
        
    Returns:
        Optional[List[float]]: Введенный массив вещественных чисел или None если ввод был отменен
    """
    array = input_array(size, as_int=False, validator=validator)
    return [float(val) for val in array] if array is not None else None

def input_int_array(size: int,
                  validator: Optional[Callable[[str], Tuple[bool, str]]] = None) -> Optional[List[int]]:
    """
    Интерактивный ввод массива целых чисел.
    
    Args:
        size (int): Размер массива
        validator (callable, optional): Функция для проверки вводимых значений
        
    Returns:
        Optional[List[int]]: Введенный массив целых чисел или None если ввод был отменен
    """
    array = input_array(size, as_int=True, validator=validator)
    return [int(float(val)) for val in array] if array is not None else None

# Example usage
if __name__ == "__main__":
    def custom_validator(value: str) -> Tuple[bool, str]:
        try:
            num = float(value)
            if -100 <= num <= 100:
                return True, ""
            return False, "Значение должно быть от -100 до 100"
        except ValueError:
            return False, "Введите корректное число"
    
    print("Ввод массива из 5 элементов (значения от -100 до 100):")
    
    # Example for float input
    result = input_float_array(5, validator=custom_validator)
    
    if result is not None:
        print("\nИтоговый массив:")
        print(result)
    else:
        print("\nВвод отменен")