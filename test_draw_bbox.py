import tensorflow as tf
import matplotlib.pyplot as plt
import os
import json
import subprocess
from scipy.misc import imread

from train import build_forward
from utils import train_utils
from utils.annolist import AnnotationLib as al
from utils.stitch_wrapper import stitch_rects
from utils.train_utils import add_rectangles
from utils.rect import Rect
from utils.stitch_wrapper import stitch_rects
from evaluate import add_rectangles
import cv2
import glob

hypes_file = './hypes/lstm_rezoom.json'
iteration = 30000
with open(hypes_file, 'r') as f:
    H = json.load(f)

#true_json = './new_labels/validation20.json'
#pred_json = './output/%d_val_%s.json' % (iteration, os.path.basename(hypes_file).replace('.json', ''))
#true_annos = al.parse(true_json)
test_imgs = glob.glob("test_stg1/rescaled/*_resized.jpg")

tf.reset_default_graph()
x_in = tf.placeholder(tf.float32, name='x_in', shape=[H['image_height'], H['image_width'], 3])
if H['use_rezoom']:
    pred_boxes, pred_logits, pred_confidences, pred_confs_deltas, pred_boxes_deltas = build_forward(H, tf.expand_dims(x_in, 0), 'test', reuse=None)
    grid_area = H['grid_height'] * H['grid_width']
    pred_confidences = tf.reshape(tf.nn.softmax(tf.reshape(pred_confs_deltas, [grid_area * H['rnn_len'], 2])), [grid_area, H['rnn_len'], 2])
    if H['reregress']:
        pred_boxes = pred_boxes + pred_boxes_deltas
else:
    pred_boxes, pred_logits, pred_confidences = build_forward(H, tf.expand_dims(x_in, 0), 'test', reuse=None)

saver = tf.train.Saver()
with tf.Session() as sess:
    sess.run(tf.initialize_all_variables())
    saver.restore(sess, '/home/craig/Desktop/tensorbox/output/lstm_rezoom_2016_12_26_00.02/save.ckpt-30000')
    annolist = al.AnnoList()
    import time; t = time.time()
    for i in range(0, len(test_imgs)):
        true_anno = test_imgs[i]
        img = imread(test_imgs[i])
        feed = {x_in: img}
        (np_pred_boxes, np_pred_confidences) = sess.run([pred_boxes, pred_confidences], feed_dict=feed)
        pred_anno = al.Annotation()
        pred_anno.imageName = true_anno.split('/')[2]
        new_img, rects = add_rectangles(H, [img], np_pred_confidences, np_pred_boxes,
                                        use_stitching=True, rnn_len=H['rnn_len'], min_conf=0.7,
                                        show_suppressed=False)
        pred_anno.rects = rects
        annolist.append(pred_anno)
        fig = plt.figure(figsize=(12, 12))
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        plt.axis('off')
        ax.set_axis_off()
        fig.add_axes(ax)
        plt.imshow(new_img)
        fig.savefig('output/test_image_results/image%s.png' %(i))
        plt.close(fig)   # save the figure to file


#annolist.save(pred_json)
#iou_threshold = 0.2
#rpc_cmd = './utils/annolist/doRPC.py --minOverlap %f %s %s' % (iou_threshold, true_json, pred_json)
#print('$ %s' % rpc_cmd)
#rpc_output = subprocess.check_output(rpc_cmd, shell=True)
#print(rpc_output)
#txt_file = [line for line in rpc_output.split('\n') if line.strip()][-1]
#output_png = 'output/results.png'
#plot_cmd = './utils/annolist/plotSimple.py %s --output %s' % (txt_file, output_png)
#print('$ %s' % plot_cmd)
#plot_output = subprocess.check_output(plot_cmd, shell=True)
#from IPython.display import Image
#Image(filename=output_png) 
