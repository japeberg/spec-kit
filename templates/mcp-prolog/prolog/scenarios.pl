% scenarios.pl - Test case generation scenarios
%
% This file defines predicates for generating test cases.
% Used by the MCP server to create boundary cases and examples.

:- ['domain.pl'].

% Generate valid user scenarios
valid_user(UserId, Role) :-
    between(1, 1000, UserId),
    member(Role, [admin, editor, viewer]).

% Generate invalid user scenarios
invalid_user(UserId, Role) :-
    (UserId =< 0 ; UserId > 1000),
    member(Role, [admin, editor, viewer, invalid_role]).

invalid_user(UserId, Role) :-
    between(1, 1000, UserId),
    \+ member(Role, [admin, editor, viewer]).

% Add your own scenario generators here
% For example:
% - Edge cases
% - Boundary conditions
% - Invalid state combinations
% - Complex multi-entity scenarios
