from copy import deepcopy
from ...boards import Square, State


def deepcopy_board(function):
    def with_copied_board(macroboard, *args):
        return function(deepcopy(macroboard), *args)
    return with_copied_board


@deepcopy_board
def winning_move(macroboard):
    """
    Returns a valid winning move for the macroboard, if present.
    Returns None, otherwise
    """
    moves = macroboard.available_moves
    for px, py in moves:
        macroboard.make_move(px, py)
        if macroboard.has_a_winner:
            return (px, py)
        macroboard.undo_last_move()
    return None


@deepcopy_board
def losing_moves(macroboard):
    """
    Returns a list of the moves, after which the other player can win.
    """
    moves = macroboard.available_moves
    losing = []
    for px, py in moves:
        macroboard.make_move(px, py)
        if winning_move(macroboard) is not None:
            losing.append((px, py))
        macroboard.undo_last_move()
    return losing


def not_losing_moves(macroboard):
    """
    Returns a list of the moves, after which the other player cannot win.
    """
    moves = macroboard.available_moves
    losing = losing_moves(macroboard)
    return [move for move in moves if move not in losing]


def player_to_state(player):
    if player == Square.X:
        return State.X_WON
    if player == Square.O:
        return State.O_WON
    raise ValueError('Invalid player')

CENTRAL = (1, 1)
CORNERS = [(0, 0), (0, 2), (2, 0), (2, 2)]

SCORE_FOR_WIN = 10000
SCORE_FOR_WON_BOARD = 5
SCORE_FOR_WON_CENTRAL_BOARD = 10
SCORE_FOR_WON_CORNER_BOARD = 3

SCORE_FOR_TWO_SQUARES_IN_A_ROW = 2
SCORE_FOR_TWO_BOARDS_IN_A_ROW = 4

SCORE_FOR_SQUARE_IN_CENTRAL = 3
SCORE_FOR_CENTRAL_IN_BOARD = 2  # 3

SCORE_FOR_CAN_PLAY_ANYWHERE = 2


def two_squares_in_a_row(microboard, player):
    """
    If the player has two squares on the microboard, that are in the same
    row/column/diagonal and the third square there is empty, that makes a 'two'
    Return the number of 'twos' for the microboard.
    """
    twos = 0
    for line in microboard.lines():
        if line.count(player) == 2 and line.count(Square.EMPTY) == 1:
            twos += 1
    return twos


def two_boards_in_a_row(macroboard, player):
    """
    If the player has won two microboards, that are in the same row/column/diag
    and the third board there is not dead, that makes a 'two'
    Return the number of 'twos' for the macroboard.
    """
    twos = 0
    state = player_to_state(player)
    for line in macroboard.state_lines():
        if line.count(state) == 2 and line.count(State.IN_PROGRESS) == 1:
            twos += 1
    return twos


def squares_won(microboard, player):
    """
    Return the number of squares won by the player on the microboard.
    """
    return sum(map(lambda line: line.count(player), microboard.export_grid()))


def score_microboard(microboard, i, j, player):
    """
    Return the heuristics score of the player for the microboard.
    """
    score = 0
    if microboard.winner() == player:
        score += SCORE_FOR_WON_BOARD
        if (i, j) == CENTRAL:
            score += SCORE_FOR_WON_CENTRAL_BOARD
        if (i, j) in CORNERS:
            score += SCORE_FOR_WON_CORNER_BOARD
        return score
    if microboard.state != State.IN_PROGRESS:
        return score
    if (i, j) == CENTRAL:
        score += squares_won(microboard, player) * SCORE_FOR_SQUARE_IN_CENTRAL
    if microboard.grid[CENTRAL[0]][CENTRAL[1]] == player:
        score += SCORE_FOR_CENTRAL_IN_BOARD
    twos = two_squares_in_a_row(microboard, player)
    score += twos * SCORE_FOR_TWO_SQUARES_IN_A_ROW
    return score


def score_macroboard(macroboard, player):
    """
    Return the heuristics score of the player for the macroboard.
    """
    if macroboard.winner() == player:
        return SCORE_FOR_WIN
    score = 0
    for i in range(macroboard.SIZE):
        for j in range(macroboard.SIZE):
            score += score_microboard(macroboard.boards[i][j], i, j, player)
    twos = two_boards_in_a_row(macroboard, player)
    score += twos * SCORE_FOR_TWO_BOARDS_IN_A_ROW
    if player == macroboard.get_on_turn():
        if macroboard.can_play_on_all_active():
            score += SCORE_FOR_CAN_PLAY_ANYWHERE
    return score


def score(macroboard):
    """
    Return the difference of the heuristics' scores of the players
    for the macoboard. The player currently on turn has the positive value,
    and the player not on turn - the negative.
    """
    first_player = macroboard.get_on_turn()
    second_player = Square.O if first_player == Square.X else Square.X
    first_player_score = score_macroboard(macroboard, first_player)
    second_player_score = score_macroboard(macroboard, second_player)
    # print(first_player_score, second_player_score)
    return first_player_score - second_player_score


def greedy_score(macroboard):
    """
    Return greedy heuristics score for the macroboard.
    Greedy for microboards.
    """
    player = macroboard.get_on_turn()
    other = Square.O if player == Square.X else Square.X
    if macroboard.winner() == player:
        return SCORE_FOR_WIN
    score = 0
    for (i, j) in macroboard.dead_boards:
        if macroboard.boards[i][j].winner() == player:
            score += SCORE_FOR_WON_BOARD
        if macroboard.boards[i][j].winner() == other:
            score -= SCORE_FOR_WON_BOARD
    return score
