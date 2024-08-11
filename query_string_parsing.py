"""Provides functions to build search queries from command strings."""

import text_query
import enum


class TokenizerFSMState(enum.Enum):
    PARSING_COMMAND = 0,
    PARSING_ELSE = 1,
    PARSING_AND = 2,
    PARSING_OR = 3


def _tokenize_command_str(command: str) -> list[str]:
    tokens = []
    paren_depth = 0
    state = TokenizerFSMState.PARSING_ELSE

    command_str = ''

    # Parse the command with a finite-state machine.
    idx = 0
    while idx < len(command):
        if state == TokenizerFSMState.PARSING_ELSE:
            char = command[idx]

            if char == '&' or char == '|':
                tokens.append(char)
                idx = idx + 1

            elif '(' == char:
                tokens.append(f'({paren_depth}')
                paren_depth = paren_depth + 1
                idx = idx + 1

            elif ')' == char:
                paren_depth = paren_depth - 1
                if paren_depth < 0:
                    raise ValueError('Invalid parentheses in string.')
                tokens.append(f'){paren_depth}')
                idx = idx + 1
            elif char.isspace():
                idx = idx + 1

            else:  # Otherwise, this is a command.
                state = TokenizerFSMState.PARSING_COMMAND

        elif TokenizerFSMState.PARSING_COMMAND == state:
            char = command[idx]
            if char in '()':  # If found a special character, return to that parsing state.
                state = TokenizerFSMState.PARSING_ELSE
                tokens.append(command_str.strip())
                command_str = ''
            else:
                command_str = f'{command_str}{char}'
                idx = idx + 1

                # If the last word of input has been an AND or an OR, then this is no longer / has never been a command,
                # but is an AND or an OR.
                stripped = command_str.strip()
                split = command_str.split()
                if stripped == 'and':
                    tokens.append('&')
                    command_str = ''
                    state = TokenizerFSMState.PARSING_ELSE
                    idx = idx + 1
                elif stripped == 'or':
                    tokens.append('|')
                    command_str = ''
                    state = TokenizerFSMState.PARSING_ELSE
                    idx = idx + 1
                elif split[-1] == 'and':
                    tokens.append(' '.join(split[0:len(split)-1]))
                    command_str = ''
                    tokens.append('&')
                    state = TokenizerFSMState.PARSING_ELSE
                    idx = idx + 1
                elif split[-1] == 'or':
                    tokens.append(' '.join(split[0:len(split)-1]))
                    command_str = ''
                    tokens.append('|')
                    state = TokenizerFSMState.PARSING_ELSE
                    idx = idx + 1


    if paren_depth != 0:
        raise ValueError('Invalid parentheses in string.')
    if command_str != '':
        tokens.append(command_str)

    return tokens


class CMDToQueryFSMState(enum.Enum):
    DEFAULT_STATE = 0,
    PARSING_CASE = 1,
    PARSING_NUMBER = 2,
    PARSING_GENDER = 3


def _cmd_to_query(cmd: str) -> text_query.TextQuery:
    """Converts a command into a text query."""
    cmd_tokens = cmd.split()
    if 0 == len(cmd_tokens):
        raise ValueError('Invalid empty command given.')

    # The first token will always be the lexeme, so just remove it off-the-top.
    lexeme = cmd_tokens[0]
    cmd_tokens = cmd_tokens[1:]

    # Declare the fields which may be written.
    case = None
    number = None
    gender = None

    state = CMDToQueryFSMState.DEFAULT_STATE
    i = 0
    while i < len(cmd_tokens):
        token = cmd_tokens[i]
        # Default case
        if CMDToQueryFSMState.DEFAULT_STATE == state:
            if '--case' == token:
                state = CMDToQueryFSMState.PARSING_CASE
                i = i + 1
            elif '--number' == token:
                state = CMDToQueryFSMState.PARSING_NUMBER
                i = i + 1
            elif '--gender' == token:
                state = CMDToQueryFSMState.PARSING_GENDER
                i = i + 1
            else:  # Invalid token
                raise ValueError(f'Syntax: invalid search token, "{token}"')
        # Parsing case
        elif CMDToQueryFSMState.PARSING_CASE == state:
            if case is not None:
                raise ValueError('Syntax: cannot define case twice')
            if token not in ['nominative', 'genitive', 'dative', 'accusative']:
                raise ValueError(f'Value: not a case, "{token}"')
            case = token
            i = i + 1
            state = CMDToQueryFSMState.DEFAULT_STATE
        # Parsing number
        elif CMDToQueryFSMState.PARSING_NUMBER == state:
            if number is not None:
                raise ValueError('Syntax: cannot define number twice')
            if token not in ['singular', 'plural', 'dual']:
                raise ValueError(f'Value: not a number, "{token}"')
            number = token
            i = i + 1
            state = CMDToQueryFSMState.DEFAULT_STATE
        # Parsing gender
        elif CMDToQueryFSMState.PARSING_GENDER == state:
            if gender is not None:
                raise ValueError('Syntax: cannot define gender twice')
            if token not in ['masculine', 'feminine', 'neuter']:
                raise ValueError(f'Value: not a gender, "{token}"')
            gender = token
            i = i + 1
            state = CMDToQueryFSMState.DEFAULT_STATE

    # Error out if we ended in an invalid state.
    if state == CMDToQueryFSMState.PARSING_CASE:
        raise ValueError('Syntax: lacking argument to --case')
    elif state == CMDToQueryFSMState.PARSING_NUMBER:
        raise ValueError('Syntax: lacking argument to --number')
    elif state == CMDToQueryFSMState.PARSING_GENDER:
        raise ValueError('Syntax: lacking argument to --gender')

    # Construct the final query.
    query = text_query.LexemeQuery(lexeme)
    query.case = case
    query.number = number
    query.gender = gender

    return query


def _is_cmd(token: str) -> bool:
    return token not in ['&', '|']


def _replace_parens_with_sublists(tokens: list[str]) -> list:
    """Replaces tokens containing parentheses into sublists, for easier construction into a tree later."""
    result = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if type(token) is str and token.startswith('('):
            paren_num = int(token[1:])
            closing_paren_str = f'){paren_num}'
            j = i
            while j < len(tokens):
                if tokens[j] == closing_paren_str:
                    if i + 1 == j:
                        raise ValueError('Syntax: cannot have empty parentheses.')
                    sub_tokens = tokens[i + 1:j]
                    sub_query = _replace_parens_with_sublists(sub_tokens)
                    result.append(sub_query)
                    i = j
                    break
                j = j + 1
        else:
            result.append(token)
        i = i + 1
    return result


def _argument_to_query(arg) -> text_query.TextQuery:
    """Converts the given op argument to a query. This is necessary because the arguments can be of different types:
    a token list, an already-formed query, etc."""
    if issubclass(type(arg), text_query.TextQuery):
        return arg
    elif type(arg) is str and _is_cmd(arg):
        return _cmd_to_query(arg)
    elif type(arg) is list:
        return _tokens_list_to_query(arg)
    else:
        raise ValueError(f'Syntax: unexpected argument to op, {arg}')


def _tokens_list_to_query(tokens: list[str]) -> text_query.TextQuery:
    """Converts a list of tokens to a query."""

    # Get rid of the parentheses, for easier processing.
    no_parens_list = _replace_parens_with_sublists(tokens)

    # Recursively call this function on the arguments of ANDs
    and_occurrences = [i for i, x in enumerate(no_parens_list) if '&' == x]
    for i in reversed(and_occurrences):
        # We loop backwards because we want to construct our objects in such a way that the leftmost is on the top
        # of the tree. Also, because we're moving backwards, we can retain our indices without corrupting the list.
        if i == 0 or i == len(no_parens_list):
            raise ValueError('Syntax: no argument to &.')
        lhs = _argument_to_query(no_parens_list[i-1])
        rhs = _argument_to_query(no_parens_list[i+1])
        and_query = text_query.AndQuery(lhs, rhs)
        del no_parens_list[i-1:i+2]
        no_parens_list.insert(i-1, and_query)

    # Recursively call this function on the arguments of ORs
    or_occurrences = [i for i, x in enumerate(no_parens_list) if '|' == x]
    for i in reversed(or_occurrences):
        # We loop backwards because we want to construct our objects in such a way that the leftmost is on the top
        # of the tree. Also, because we're moving backwards, we can retain our indices without corrupting the list.
        if i == 0 or i == len(no_parens_list):
            raise ValueError('Syntax: no argument to &.')
        lhs = _argument_to_query(no_parens_list[i - 1])
        rhs = _argument_to_query(no_parens_list[i + 1])
        and_query = text_query.OrQuery(lhs, rhs)
        del no_parens_list[i - 1:i + 2]
        no_parens_list.insert(i - 1, and_query)

    # This should never happen at this point, but if there's more than one element in the list, we've hit an error.
    if 1 != len(no_parens_list):
        raise ValueError("Bug: Something's on fire. Tell Andrew!!!")
    return _argument_to_query(no_parens_list[0])


def to_query(command: str) -> text_query.TextQuery:
    """Converts the command into a query."""
    # Get the tokens in the command string.
    tokens = _tokenize_command_str(command)
    return _tokens_list_to_query(tokens)


if __name__ == '__main__':
    # Test tokenizer.
    print(to_query('(please work | λογος) | αληθινος & ((ρημα & lmao) | lol)'))
