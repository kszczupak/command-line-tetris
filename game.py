import curses
from time import time, sleep
from collections import defaultdict

from pieces import *


def main(stdscr):
	"""
	Main function which controls Tetris game logic.
	:param stdscr: standard curses screen; will be supplied by wrapper function
	"""
	setup_main_window(stdscr)
	height, width = stdscr.getmaxyx()

	play_window = setup_play_window(width)
	stats = setup_statistics(width)
	next_piece_window = setup_next_piece_window(width)
	time_interval, score = setup_score(width)

	block = get_random_piece()()
	stats.send(block)
	next_piece = get_random_piece()

	draw_next_piece(next_piece_window, next_piece)
	draw_piece(play_window, block)

	stack = {
		"positions": dict(),
		"previous_positions": None
	}

	timer = time()

	while True:
		# positions after left/right movement or rotation
		candidate_positions = None
		# positions after falling down (by pressing down key or due to completed interval)
		advanced_positions = None

		# this method is non-blocking (set in setup_main_window)
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
			# interval is completed, setup next cycle
			advanced_positions = block.advance()
			timer = time()

		if candidate_positions:
			if validate_positions(candidate_positions, stack):
				block.accept_move()
				re_draw_piece(play_window, block)
			else:
				block.reject_move()

		if advanced_positions:
			if is_inside_stack(advanced_positions, stack):
				affected_lines = increase_stack(block, stack)

				if 1 in affected_lines:
					# game over
					end_animation(play_window)
					break

				cleared_lines = check_cleared_lines(stack, affected_lines)

				if cleared_lines:
					clear_line_animation(play_window, cleared_lines)
					clear_lines(cleared_lines, stack)
					time_interval = score.send(len(cleared_lines))

				block = next_piece()
				stats.send(block)
				next_piece = get_random_piece()
				draw_next_piece(next_piece_window, next_piece)

				draw_stack(play_window, stack)
			else:
				block.accept_move()

			re_draw_piece(play_window, block)


"""
===================Drawing functions===================
"""


def setup_main_window(window):
	window.keypad(True)
	window.nodelay(True)
	window.refresh()
	init_colors()
	title = "Command Line Tetris"
	height, width = window.getmaxyx()
	window.addstr(2, width // 2 - len(title) // 2, title)

	# no cursor
	curses.curs_set(0)


PLAY_AREA_WIDTH = 10
PLAY_AREA_HEIGHT = 20
START_LINE = 4


def setup_play_window(console_width):
	# height and width of the new window + 2 to account for the borders
	play_window = curses.newwin(
		PLAY_AREA_HEIGHT + 2, 2 * PLAY_AREA_WIDTH + 2, START_LINE, console_width // 2 - PLAY_AREA_WIDTH
	)
	play_window.border()

	return play_window


STATS_AREA_WIDTH = 7
STATS_AREA_HEIGHT = 20
STATS_PIECES = (T_Piece, J_Piece, Z_Piece, Square, S_Piece, L_Piece, LongBar)


def setup_statistics(console_width):
	statistics_window = curses.newwin(
		STATS_AREA_HEIGHT + 2, 2 * STATS_AREA_WIDTH + 2, START_LINE, console_width // 2 - PLAY_AREA_WIDTH - 2 * STATS_AREA_WIDTH - 2
	)
	statistics_window.border()
	statistics_window.addstr(1, 3, "STATISTICS")
	statistics_window.refresh()

	line = 2

	for piece_class in STATS_PIECES:
		piece = piece_class(initial_rotation_block_position=(line, 2))

		if isinstance(piece, LongBar) or isinstance(piece, Square):
			# ugly way of adjusting Long Bar and Square
			x_offset = 1
		else:
			x_offset = 0

		draw_piece(statistics_window, piece, x_offset)
		line += 3

	stats = statistics_gen(statistics_window)
	next(stats)

	return stats


def statistics_gen(window):
	"""
	Corutine which maintains statistics and updates statistic window. Piece which shall be included in statistics is
	expected to be send to this corutine.
	"""
	def re_draw_stats():
		line = 2
		for piece_class in STATS_PIECES:
			piece_stats = stats[piece_class()]
			window.addstr(line, 10, f"{piece_stats:03}")
			line += 3

		window.refresh()

	stats = defaultdict(int)
	while True:
		re_draw_stats()
		piece = yield
		stats[piece] += 1


NEXT_PIECE_AREA_WIDTH = 4
NEXT_PIECE_AREA_HEIGHT = 5


def setup_next_piece_window(console_width):
	next_piece_window = curses.newwin(
		NEXT_PIECE_AREA_HEIGHT + 2, 2 * NEXT_PIECE_AREA_WIDTH + 2, START_LINE, console_width // 2 + PLAY_AREA_WIDTH + 2
	)
	next_piece_window.border()
	next_piece_window.addstr(1, 3, "NEXT")
	next_piece_window.refresh()

	return next_piece_window


SCORE_AREA_WIDTH = 4
SCORE_AREA_HEIGHT = 8


def setup_score(console_width):
	score_window = curses.newwin(
		SCORE_AREA_HEIGHT + 2, 2 * SCORE_AREA_WIDTH + 2, START_LINE + 8, console_width // 2 + PLAY_AREA_WIDTH + 2
	)
	score_window.border()
	score_window.addstr(1, 1, "SCORE:", curses.A_BOLD and curses.A_UNDERLINE)
	score_window.addstr(4, 1, "LINES:", curses.A_BOLD and curses.A_UNDERLINE)
	score_window.addstr(7, 1, "LEVEL:", curses.A_BOLD and curses.A_UNDERLINE)
	score_window.refresh()

	score = score_gen(score_window)
	initial_time_interval = next(score)

	return initial_time_interval, score


INITIAL_TIME_INTERVAL = 1


def score_gen(window):
	"""
	Corutine which maintains score, level, number of cleared line and current time interval. Updated time interval is
	returned as a response to sending cleared lines count.
	"""
	def update_score_window():
		window.addstr(2, 2, f"{score:05}")
		window.addstr(5, 2, f"{lines:03}")
		window.addstr(8, 2, f"{lvl:03}")
		window.refresh()

	def calculate_score(lines_cnt):
		# scoring system taken from https://tetris.fandom.com/wiki/Scoring
		if lines_cnt == 4:
			# Tetris
			return 1200 * (lvl + 1)
		if lines_cnt == 3:
			return 300 * (lvl + 1)
		if lines_cnt == 2:
			return 100 * (lvl + 1)

		return 40 * (lvl + 1)

	def update_time_interval():
		offset = lvl * 0.1
		if INITIAL_TIME_INTERVAL > offset:
			return INITIAL_TIME_INTERVAL - offset

		return current_time_interval

	current_time_interval = INITIAL_TIME_INTERVAL  # [s]
	score = 0
	lines = 0
	lvl = 0

	while True:
		update_score_window()
		nbr_of_cleared_lines = yield current_time_interval
		lines += nbr_of_cleared_lines
		score += calculate_score(nbr_of_cleared_lines)
		lvl = lines // 10
		current_time_interval = update_time_interval()


# associated given piece with color pairs defined in init_colors
COLOR_MAP = {
	T_Piece(): 1,
	J_Piece(): 2,
	Z_Piece(): 3,
	Square(): 4,
	S_Piece(): 5,
	L_Piece(): 6,
	LongBar(): 7
}


def init_colors():
	"""
	Initializes curses colors for all pieces
	"""
	curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
	curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)


def re_draw_piece(window, piece: AbstractPiece):
	previous_positions = piece.previous_positions

	if previous_positions:
		for old_y, old_x in previous_positions:
			window.addch(old_y, 2 * old_x + 1, " ")
			window.addch(old_y, 2 * old_x + 2, " ")

	draw_piece(window, piece)


def draw_piece(window, piece, x_offset=1):
	for new_y, new_x in piece.current_positions:
		# two curses.ACS_CKBOARD can be used also as one basic square
		# first and last columns serve as borders, so +1/+2 offsets needs to be used
		# to account for that
		color = COLOR_MAP[piece]
		window.addch(new_y, 2 * new_x + x_offset, "[", curses.color_pair(color))
		window.addch(new_y, 2 * new_x + x_offset + 1, "]", curses.color_pair(color))

	window.refresh()


def draw_next_piece(window, piece_class):
	def erase_piece():
		for old_y in range(2, NEXT_PIECE_AREA_HEIGHT):
			for old_x in range(NEXT_PIECE_AREA_WIDTH):
				window.addch(old_y, 2 * old_x + 1, " ")
				window.addch(old_y, 2 * old_x + 2, " ")

	erase_piece()

	next_piece = piece_class(initial_rotation_block_position=(3, 2))

	if isinstance(next_piece, LongBar) or isinstance(next_piece, Square):
		# ugly way of adjusting Long Bar and Square to fit in the preview window
		x_offset = 1
	else:
		x_offset = 0

	draw_piece(window, next_piece, x_offset)


def draw_stack(window, stack):
	if stack['previous_positions']:
		for y, x in stack['previous_positions']:
			window.addch(y, 2 * x + 1, " ")
			window.addch(y, 2 * x + 2, " ")

		stack['previous_positions'] = None

	for (y, x), color in stack['positions'].items():
		window.addch(y, 2 * x + 1, "[", curses.color_pair(color))
		window.addch(y, 2 * x + 2, "]", curses.color_pair(color))

	window.refresh()


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


"""
===================Game logic functions===================
"""


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


def increase_stack(piece, stack):
	affected_lines = set()
	color = COLOR_MAP[piece]

	for position in piece.current_positions:
		stack['positions'][position] = color
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

	new_positions = dict()

	max_line = max(lines)
	# update remaining stack positions
	for position, color in stack['positions'].items():
		y, x = position

		if y in lines:
			continue

		if y > max_line:
			# current position is below cleared lines
			# position doesn't need to be updated
			new_positions[position] = color
		else:
			new_position = (y + count_lines_above(y), x)
			new_positions[new_position] = color

	stack['previous_positions'] = stack['positions']
	stack['positions'] = new_positions


if __name__ == '__main__':
	curses.wrapper(main)
