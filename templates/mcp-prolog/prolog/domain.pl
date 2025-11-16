% domain.pl - Basic domain model for Spec Kit projects
%
% This file defines the core domain concepts for your project.
% Customize these predicates to match your specific domain.

% Example: user(Id, Role)
% Defines valid users with their roles
user(Id, Role) :-
    integer(Id),
    member(Role, [admin, editor, viewer]).

% Example: Capability predicates
% Define what actions different roles can perform
can_delete(UserId) :-
    user(UserId, admin).

can_modify(UserId) :-
    user(UserId, Role),
    member(Role, [admin, editor]).

can_view(UserId) :-
    user(UserId, _).

% Add your own domain predicates here
% For example:
% - Entity relationships
% - Business rules
% - Valid state transitions
% - Access control rules
