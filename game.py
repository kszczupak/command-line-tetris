import curses
from time import time, sleep

from pieces import *


PLAY_AREA_WIDTH = 10
PLAY_AREA_HEIGHT = 20

NEXT_PIECE_AREA_WIDTH = 4
NEXT_PIECE_AREA_HEIGHT = 5


def draw_piece(window, piece: AbstractPiece):
		previous_positions = piece.previous_positions

		if previous_positions:
			for old_y, old_x in previous_positions:
				window.addch(old_y, 2 * old_x + 1, " ")
				window.addch(old_y, 2 * old_x + 2, " ")

		for new_y, new_x in piece.current_positions:
			# two curses.ACS_CKBOARD can be used also as one basic square
			# first and last columns serve as borders, so +1 and +2 offsets needs to be used
			# to account for that
			window.addch(new_y, 2 * new_x + 1, "[")
			window.addch(new_y, 2 * new_x + 2, "]")

		window.refresh()


def draw_next_piece(window, piece_class):
	def erase_piece():
		for old_y in range(2, NEXT_PIECE_AREA_HEIGHT):
			for old_x in range(NEXT_PIECE_AREA_WIDTH):
				window.addch(old_y, 2 * old_x + 1, " ")
				window.addch(old_y, 2 * old_x + 2, " ")

	erase_piece()

	next_piece = piece_class(initial_rotation_block_position=(3, 2))

	for y, x in next_piece.current_positions:
		if isinstance(next_piece, LongBar) or isinstance(next_piece, Square):
			# ugly way of adjusting Long Bar and Square to fit in the preview window
			x_offset_1 = 1
			x_offset_2 = 2
		else:
			x_offset_1 = 0
			x_offset_2 = 1

		window.addch(y, 2 * x + x_offset_1, "[")
		window.addch(y, 2 * x + x_offset_2, "]")

	window.refresh()


def draw_stack(window, stack):
	if stack['previous_positions']:
		for y, x in stack['previous_positions']:
			window.addch(y, 2 * x + 1, " ")
			window.addch(y, 2 * x + 2, " ")

		stack['previous_positions'] = None

	for y, x in stack['positions']:
		window.addch(y, 2 * x + 1, "[")
		window.addch(y, 2 * x + 2, "]")

	window.refresh()


def validate_positions(requested_positions, stack):
	for candidate_y, candidate_x in requested_positions:
		if candidate_y <= 0 or candidate_y > PLAY_AREA_HEIGHT:
			return False

		if candidate_x < 0 or candidate_x >= PLAY_AREA_WIDTH:
			return False

		if (candidate_y, candidate_x) in stack['positions']:
			return False

	return True


def is_inside_stack(requested_positions, stack):
	for candidate_point in requested_positions:
		if candidate_point in stack['positions']:
			return True

		candidate_y, _ = candidate_point

		if candidate_y > PLAY_AREA_HEIGHT:
			# last row
			return True

	return False


def increase_stack(positions, stack):
	affected_lines = set()

	for position in positions:
		stack['positions'].add(position)
		line, _ = position
		affected_lines.add(line)

	return affected_lines


def check_cleared_lines(stack, affected_lines):
	cleared_lines = list()

	for line in affected_lines:
		line_cleared = True
		for x in range(PLAY_AREA_WIDTH):
			if (line, x) not in stack['positions']:
				line_cleared = False
				break

		if line_cleared:
			cleared_lines.append(line)

	return cleared_lines


def clear_lines(lines, stack):
	def count_lines_above(line):
		cnt = 0

		for cleared_line in lines:
			if line < cleared_line:
				cnt += 1

		return cnt

	new_positions = set()

	max_line = max(lines)
	# update remaining stack positions
	for position in stack['positions']:
		y, x = position

		if y in lines:
			continue

		if y > max_line:
			# current position is below cleared lines
			# position doesn't need to be updated
			new_positions.add(position)
		else:
			new_position = (y + count_lines_above(y), x)
			new_positions.add(new_position)

	stack['previous_positions'] = stack['positions']
	stack['positions'] = new_positions


def clear_line_animation(window, lines):
	def fill_with(char):
		for line in lines:
			for x in range(PLAY_AREA_WIDTH):
				window.addch(line, 2 * x + 1, char)
				window.addch(line, 2 * x + 2, char)

		window.refresh()

	def animation_cycle():
		fill_with(curses.ACS_CKBOARD)
		sleep(0.1)
		fill_with(" ")
		sleep(0.1)

	if len(lines) == 4:
		# tetris scored
		nbr_of_cycles = 3
	elif len(lines) == 3:
		nbr_of_cycles = 2
	else:
		nbr_of_cycles = 1

	for _ in range(nbr_of_cycles):
		animation_cycle()


def end_animation(window):
	for y in range(1, PLAY_AREA_HEIGHT + 1):
		for x in range(PLAY_AREA_WIDTH):
			window.addch(y, 2 * x + 1, curses.ACS_CKBOARD)
			window.addch(y, 2 * x + 2, curses.ACS_CKBOARD)
			window.refresh()
			sleep(0.02)

	sleep(1)


def main(stdscr):
	stdscr.keypad(True)
	stdscr.nodelay(True)
	height, width = stdscr.getmaxyx()
	stdscr.refresh()
	stdscr.addstr(1, width//2, "Command Line T.")

	# no cursor
	curses.curs_set(0)

	# height and width of the new window + 2 to account for the borders
	play_window = curses.newwin(PLAY_AREA_HEIGHT + 2,  2 * PLAY_AREA_WIDTH + 2, 5, width//2 - 10)
	play_window.border()

	# 5 (with text) x 4
	next_piece_window = curses.newwin(5 + 2,  2 * 4 + 2, 5 + 8, width//2 + 12)
	next_piece_window.border()
	next_piece_window.addstr(1, 3, "NEXT")
	next_piece_window.refresh()

	block = get_random_piece()()
	next_piece = get_random_piece()

	draw_next_piece(next_piece_window, next_piece)

	draw_piece(play_window, block)

	stack = {
		"positions": set(),
		"previous_positions": None
	}

	timer = time()
	time_interval = 1

	while True:
		candidate_positions = None
		advanced_positions = None

		c = stdscr.getch()

		if c == curses.KEY_RIGHT:
			candidate_positions = block.move_right()
		elif c == curses.KEY_LEFT:
			candidate_positions = block.move_left()
		elif c == curses.KEY_DOWN:
			advanced_positions = block.advance()
		elif c == ord('a'):
			candidate_positions = block.rotate_clockwise()
		elif c == ord('d'):
			candidate_positions = block.rotate_anti_clockwise()
		elif c == ord('q'):
			break

		if time() - timer >= time_interval:
			advanced_positions = block.advance()
			timer = time()

		if candidate_positions:
			if validate_positions(candidate_positions, stack):
				block.accept_move()
				draw_piece(play_window, block)
			else:
				block.reject_move()

		if advanced_positions:
			if is_inside_stack(advanced_positions, stack):
				affected_lines = increase_stack(block.current_positions, stack)

				if 1 in affected_lines:
					# game over
					end_animation(play_window)
					break

				cleared_lines = check_cleared_lines(stack, affected_lines)

				if cleared_lines:
					clear_line_animation(play_window, cleared_lines)
					clear_lines(cleared_lines, stack)

				block = next_piece()
				next_piece = get_random_piece()
				draw_next_piece(next_piece_window, next_piece)

				draw_stack(play_window, stack)
			else:
				block.accept_move()

			draw_piece(play_window, block)


if __name__ == '__main__':
	curses.wrapper(main)
