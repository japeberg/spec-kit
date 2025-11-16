% queries.pl - Query predicates for MCP server integration
%
% This file provides predicates that output JSON for the MCP server.
% These are called by the Python MCP server to interact with the Prolog model.

:- ['domain.pl', 'constraints.pl', 'scenarios.pl'].
:- use_module(library(http/json)).

% Helper to emit JSON to stdout
emit_json(Term) :-
    json_write_dict(current_output, Term),
    nl.

% Generate test cases for users
generate_user_cases :-
    findall(_{type: valid, user_id: U, role: R},
        (valid_user(U, R), U =< 10),  % Limit to first 10 for brevity
        Valids),
    findall(_{type: invalid, user_id: U2, role: R2},
        invalid_user(U2, R2),  % Get sample invalid cases
        Invalids),
    append(Valids, Invalids, All),
    emit_json(_{test_cases: All}).

% Check all constraints and output as JSON
check_constraints_json :-
    check_all_constraints(Result),
    emit_json(Result).

% Generic query executor (for custom queries)
execute_query(QueryString) :-
    catch(
        (
            term_string(Query, QueryString),
            (call(Query) -> Result = success ; Result = failure),
            emit_json(_{query: QueryString, result: Result})
        ),
        Error,
        emit_json(_{query: QueryString, error: Error})
    ).
