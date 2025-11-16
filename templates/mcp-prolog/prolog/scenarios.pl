% scenarios.pl - Test case generation scenarios
%
% This file defines predicates for generating test cases.
% Used by the MCP server to create boundary cases and examples.

:- ['domain.pl'].

% Generate valid user scenarios
valid_user(UserId, Role) :-
    between(1, 1000, UserId),
    member(Role, [admin, editor, viewer]).

% Generate invalid user scenarios - negative or zero IDs
invalid_user(UserId, Role) :-
    between(-10, 0, UserId),
    member(Role, [admin, editor, viewer, invalid_role]).

% Generate invalid user scenarios - ID too large
invalid_user(UserId, Role) :-
    between(1001, 1010, UserId),
    member(Role, [admin, editor, viewer]).

% Generate invalid user scenarios - invalid role
invalid_user(UserId, invalid_role) :-
    between(1, 10, UserId).

% Add your own scenario generators here
% For example:
% - Edge cases
% - Boundary conditions
% - Invalid state combinations
% - Complex multi-entity scenarios
