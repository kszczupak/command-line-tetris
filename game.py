import curses
from time import sleep
from curses.textpad import Textbox, rectangle

from pieces import *


def main(stdscr):
	stdscr.keypad(True)
	height, width = stdscr.getmaxyx()

	stdscr.addstr(1, width//2, "Command Line T.")

	# editwin = curses.newwin(5,30, 2,1)
	# rectangle(stdscr, 1,0, 1+5+1, 1+30+1)
	rectangle(stdscr, 0, 0, 1, 1)
	curses.curs_set(0)

	# a = LongBar()
	# a = L_Piece()
	# a = J_Piece()
	# a = Square()
	# a = Z_Piece()
	a = S_Piece()
	a.debug_force_draw(stdscr)

	for i in range(3):
		a.advance()
		a.debug_force_draw(stdscr)

	a.rotate_clockwise()
	a.debug_force_draw(stdscr)

	for i in range(3, 6):
		a.advance()
		a.debug_force_draw(stdscr)

	a.rotate_clockwise()
	a.debug_force_draw(stdscr)

	a.rotate_clockwise()
	a.debug_force_draw(stdscr)

	a.rotate_clockwise()	
	a.debug_force_draw(stdscr)

	a.rotate_anti_clockwise()
	a.debug_force_draw(stdscr)

	for i in range(6, 9):
		a.advance()
		a.debug_force_draw(stdscr)

	curses.beep()
	# a = L_Piece()
	# a.debug_force_draw(stdscr)
	sleep(3)


if __name__ == '__main__':
	curses.wrapper(main)
	# a = L_Piece()
	# for i in range(3):
	# 	print(f"Tick {i}:")
	# 	print(a.blocks, end=" ")
	# 	print(f"prev: {a.previous_positions}")
	# 	print("-" * 10)
	# 	a.advance()
	# 	a.accept_move()

	# print("Rotation: rotate_clockwise")
	# a.rotate_clockwise()
	# a.accept_move()
	# print(a.blocks, end=" ")
	# print(f"prev: {a.previous_positions}")
	# print("-" * 10)

	# for i in range(3, 6):
	# 	print(f"Tick {i}:")
	# 	print(a.blocks, end=" ")
	# 	print(f"prev: {a.previous_positions}")
	# 	print("-" * 10)
	# 	a.advance()
	# 	a.accept_move()

	# print("Rotation: rotate_anti_clockwise")
	# a.rotate_anti_clockwise()
	# a.accept_move()
	# print(a.blocks, end=" ")
	# print(f"prev: {a.previous_positions}")
	# print("-" * 10)

	# for i in range(6, 9):
	# 	print(f"Tick {i}:")
	# 	print(a.blocks, end=" ")
	# 	print(f"prev: {a.previous_positions}")
	# 	print("-" * 10)
	# 	a.advance()
	# 	a.accept_move()

