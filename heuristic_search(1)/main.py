"""Điểm khởi chạy ứng dụng:  python main.py"""
from controller import Controller
from view.app_view import AppView


def main():
    view = AppView()
    Controller(view)
    view.mainloop()


if __name__ == "__main__":
    main()
