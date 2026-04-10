import pygetwindow as gw
import pyautogui


def list_open_windows():
    """Get a list of all open applications and windows."""
    return gw.getAllTitles()


def control_window(action, window_name):
    """Control a window (minimize, maximize, close) based on action specified."""
    window = gw.getWindowsWithTitle(window_name)
    if window:
        if action == "minimize":
            window[0].minimize()
        elif action == "maximize":
            window[0].maximize()
        elif action == "close":
            window[0].close()


def move_mouse(x, y):
    """Move the mouse cursor to the specified coordinates."""
    pyautogui.moveTo(x, y)


def click_mouse(button='left'):
    """Simulate a mouse click. By default, it will click the left button."""
    pyautogui.click(button=button)


def type_text(text):
    """Type the specified text using pyautogui."""
    pyautogui.write(text)


def keyboard_press(keys):
    """Press specified keyboard combinations using pyautogui."""
    pyautogui.hotkey(*keys)