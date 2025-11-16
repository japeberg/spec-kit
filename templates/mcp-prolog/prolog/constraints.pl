% constraints.pl - Invariants and validation rules
%
% This file defines constraints that must hold true for your domain model.
% These are checked by the MCP server to validate specifications.

:- ['domain.pl'].

% Invariant: all admins must be able to delete
check_admins_can_delete(Violations) :-
    findall(UserId,
        (user(UserId, admin), \+ can_delete(UserId)),
        Violations).

% Invariant: all users must be able to view
check_all_users_can_view(Violations) :-
    findall(UserId,
        (user(UserId, _), \+ can_view(UserId)),
        Violations).

% Add your own constraint checks here
% Each check should return a list of violations

% Main constraint checker - runs all checks and returns results
check_all_constraints(Result) :-
    check_admins_can_delete(AdminViolations),
    check_all_users_can_view(ViewViolations),
    Result = _{
        admins_without_delete: AdminViolations,
        users_without_view: ViewViolations
    }.
