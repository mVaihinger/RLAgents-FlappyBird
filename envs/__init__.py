from gym.envs.registration import register

for game in ['FlappyBird']:
    nondeterministic = False
    register(
        id='{}-v1'.format(game),
        entry_point='envs.environment:PLEEnv_state',
        kwargs={'game_name': game, 'display_screen':False},
        tags={'wrapper_config.TimeLimit.max_episode_steps': 10000},
        nondeterministic=nondeterministic,)