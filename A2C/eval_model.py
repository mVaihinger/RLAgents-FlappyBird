from run_ple_utils import make_ple_envs, make_ple_env
import tensorflow as tf
import os, glob
import csv
import numpy as np
import logging
import datetime

from utils_OAI import set_global_seeds, normalize_obs

def eval_model(render, nepisodes, **params):
    logger = logging.getLogger(__name__)
    logger.info('Evaluating learning algorithm...')

    logger.debug('Make Environment with seed %s' % params["seed"])
    ple_env = make_ple_env(params["env"], seed=params["seed"]) # TODO use different seed for every run!#, allow_early_resets=True)

    tf.reset_default_graph()
    set_global_seeds(params["seed"])#
    model_idx = []
    print(params["logdir"])

    if params["eval_model"] == 'final':
        f = glob.glob(os.path.join(params["logdir"], 'final_model-*.meta'))
        idx = f.find('final_model')
        f_name = f[idx:-5]
        model_idx.append(f_name)
        with tf.Session() as sess:
            OBS, PI, PI_LOGITS, pred_ac_op, pred_vf_op = restore_model(sess, logdir=params["logdir"], f_name=f_name)
            model_performance = \
                run_episodes(sess, ple_env, nepisodes, 1000, render, OBS, PI, PI_LOGITS, pred_ac_op)
            avg_performances = np.mean(model_performance)
            var_performances = np.var(model_performance)
            maximal_returns = np.max(model_performance)
        tf.reset_default_graph()

    elif params["eval_model"] == 'all':
        # Use all stored maximum performance models and the final model.
        avg_performances = []
        var_performances = []
        maximal_returns = []
        for f in glob.glob(os.path.join(params["logdir"], '*inter*.meta')):
            logger.info('Restore model: %s' % f)
            idx = f.find('_model')
            f_name = f[idx-5:-5]
            model_idx.append(f_name)
            print(f_name)
            with tf.Session() as sess:
                OBS, PI, PI_LOGITS, pred_ac_op, pred_vf_op = restore_model(sess, logdir=params["logdir"], f_name=f_name)
                logger.info('Run %s evaluation episodes' % nepisodes)
                model_performance = \
                    run_episodes(sess, ple_env, nepisodes, 1000, render, OBS, PI, PI_LOGITS, pred_ac_op)

                # Add model performance metrics
                avg_performances.append(np.mean(model_performance))
                var_performances.append(np.var(model_performance))
                maximal_returns.append(np.max(model_performance))
            tf.reset_default_graph()
    elif params["eval_model"] == 'analysis':
        # Use all stored maximum performance models and the final model.
        avg_performances = []
        std_performances = []
        maximal_returns = []
        for f in glob.glob(os.path.join(params["logdir"], '*.meta')):
            logger.info('Restore model: %s' % f)
            idx = f.find('_model')
            f_name = f[idx - 5:-5]
            model_idx.append(f_name)
            print(f_name)
            with tf.Session() as sess:
                OBS, PI, PI_LOGITS, pred_ac_op, pred_vf_op = restore_model(sess, logdir=params["logdir"], f_name=f_name)
                logger.info('Run %s evaluation episodes' % nepisodes)
                model_performance = \
                    run_episodes(sess, ple_env, nepisodes, 400, render, OBS, PI, PI_LOGITS, pred_ac_op)

                # Add model performance metrics
                avg_performances.append(np.mean(model_performance))
                std_performances.append(np.std(model_performance))
                maximal_returns.append(np.max(model_performance))
            tf.reset_default_graph()
        return model_idx, avg_performances, std_performances
    # elif params["eval_model"] == "config":
    #     # Use all stored maximum performance models and the final model.
    #     avg_performances = []
    #     var_performances = []
    #     maximal_returns = []
    #     fieldnames = ['model']
    #     for i in range(nepisodes):
    #         fieldnames.append(('eps' + str(i)))
    #     path = os.path.join(params["logdir"], 'results.csv')
    #     with open(path, "w") as csvfile:
    #         writer = csv.writer(csvfile)
    #         writer.writerow(fieldnames)
    #     models = glob.glob(os.path.join(params["logdir"], '*config_model*.meta'))
    #     models.sort()
    #     for f in models:
    #         logger.info('Restore model: %s' % f)
    #         idx = f.find('config_model')
    #         f_name = f[idx:-5]
    #         model_idx.append(f_name)
    #         with tf.Session() as sess:
    #             OBS, PI, PI_LOGITS, pred_ac_op, pred_vf_op = restore_model(sess, logdir=params["logdir"], f_name=f_name)
    #             logger.info('Run %s evaluation episodes' % nepisodes)
    #             model_performance = \
    #                 run_episodes(sess, ple_env, nepisodes, 2000, render, OBS, PI, PI_LOGITS, pred_ac_op)
    #
    #             # Add model performance metrics
    #             avg_performances.append(np.mean(model_performance))
    #             var_performances.append(np.var(model_performance))
    #             maximal_returns.append(np.max(model_performance))
    #         tf.reset_default_graph()
    #
    #         # Save episode information in csv file for further analysis each row contains nepisodes episodes using model f_name.
    #         with open(path, "a") as csvfile:  # TODO add real returns
    #             writer = csv.writer(csvfile)
    #             model_performance = [str(p) for p in model_performance]
    #             model_performance.insert(0, f_name)
    #             writer.writerow(model_performance)
    #
    logger.info('Results of the evaluation of the learning algorithm:')
    logger.info('Restored models: %s' % model_idx)
    logger.info('Average performance per model: %s' % avg_performances)
    logger.info('Performance variance per model: %s' % var_performances)
    logger.info('Maximum episode return per model: %s' % maximal_returns)

    ple_env.close()

    if len(avg_performances) > 0:
        return np.mean(avg_performances), np.mean(var_performances), np.mean(maximal_returns)
    else:
        return -5, 0, -5


def restore_model(sess, logdir, f_name):
    sess.run(tf.global_variables_initializer())
    sess.run(tf.local_variables_initializer())
    g = tf.get_default_graph()

    # restore the model
    # loader = tf.train.import_meta_graph(glob.glob(os.path.join(logdir, 'final_model-*.meta'))[0])  #TODO !!!
    loader = tf.train.import_meta_graph(glob.glob(os.path.join(logdir, 'inter_model-*.meta'))[0])

    # now variables exist, but the values are not initialized yet.
    loader.restore(sess, os.path.join(logdir, f_name))  # restore values of the variables.

    # Load operations from collections
    obs_in = tf.get_collection('inputs')
    probs_out = tf.get_collection('pi')
    pi_logits_out = tf.get_collection('pi_logit')
    predict_vf_op = tf.get_collection('val')
    predict_ac_op = tf.get_collection('step')
    return obs_in, probs_out, pi_logits_out, predict_ac_op, predict_vf_op


def run_episodes(sess, env, n_eps, n_pipes, render, obs_in, pi_out, pi_logits_out, predict_ac_op):
    logger = logging.getLogger(__name__)
    ep_length = []
    ep_return = []

    for i in range(0, n_eps): # TODO parallelize this here!
        obs = env.reset()
        obs = normalize_obs(obs)
        done = False
        total_return = 0
        total_length = 0

        while not done and (total_return < n_pipes):
            pi, pi_log, act = sess.run([pi_out, pi_logits_out, predict_ac_op], feed_dict={obs_in[0]: [obs]})
            ac = np.argmax(pi_log)
            obs, reward, done, _ = env.step(ac)
            # obs, reward, done, _ = env.step(act[0][0])
            obs = normalize_obs(obs)

            if render:
                env.render()

            total_length += 1
            total_return += reward
        # logger.debug('*****************************************')
        logger.info('Episode %s: %s, %s' % (i, total_return, total_length))
        ep_length.append(total_length)
        ep_return.append(total_return)

    return ep_return

if __name__ == '__main__':
    logdir = "/home/mara/Desktop/logs/A2C_OAI_NENVS/a2c_output"

    logger = logging.getLogger()
    ch = logging.StreamHandler()  # Handler which writes to stderr (in red)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(ch)
    fh = logging.FileHandler(os.path.join(logdir, 'eval.log'))
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)

    # Read params from hyperparameter.txt
    params = dict()
    file = open(os.path.join(logdir, 'hyperparams.txt'), 'r')
    for line in file:
        if line is '\n':
            break
        idx = line.find(':')
        p_name = line[:idx]
        p_val = line[idx + 1:]
        try:
            params[p_name] = int(p_val)
        except Exception:
            try:
                params[p_name] = float(p_val)
            except Exception:
                params[p_name] = p_val[1:-1]
    params["eval_model"] = 'config'
    params["logdir"] = logdir

    # evaluate model
    avg_perf, var_perf, max_return = eval_model(render=False, nepisodes=4, **params)
