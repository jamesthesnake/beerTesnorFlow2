
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os.path
import re
import sys
import tarfile

import numpy as np
from six.moves import urllib
import tensorflow as tf

from flask import Flask, request, Response, jsonify
app = Flask(__name__)

# import default command line flags from TensorFlow
FLAGS = tf.app.flags.FLAGS

# define directory that the model is stored in (default is the current directory)
tf.app.flags.DEFINE_string(
  'model_dir', '.',
  """Path to output_graph.pb, """
  """output_labels.txt""")

tf.app.flags.DEFINE_integer('num_top_predictions', 5,
                            """Display this many predictions.""")

# Classificaiton endpoint
@app.route("/classify", methods=["POST"])
def classify():
  predictions = dict(run_inference_on_image(request.data))
  print(predictions)
  return jsonify(predictions=predictions)



#uses tesnor flow for image recongiton


class NodeLookup(object):
  """Converts integer node ID's to human readable labels."""

  def __init__(self, label_lookup_path=None):
    if not label_lookup_path:
      label_lookup_path = os.path.join(
          FLAGS.model_dir, 'output_labels.txt')

    self.node_lookup = self.load(label_lookup_path, uid_lookup_path)

  def load(self, label_lookup_path):
    """Loads a human readable English name for each softmax node.
    Args:
      label_lookup_path: string UID to integer node ID.
    Returns:
      dict from integer node ID to human-readable string.
    """

    node_id_to_name = {}

    label_file = open(label_lookup_path)
    i = 0

    # labels are ordered from 0 to N in the lookup file

    for line in label_file:
      node_id_to_name[i] = line.strip()
      i = i + 1

    return node_id_to_name

  # return the friendly name for the given node_id
  def id_to_string(self, node_id):
    if node_id not in self.node_lookup:
      return ''
    return self.node_lookup[node_id]


def create_graph():
  """Creates a graph from saved GraphDef file and returns a saver."""
  # Creates graph from saved graph_def.pb.
  with tf.gfile.FastGFile(os.path.join(
      FLAGS.model_dir, 'output_graph.pb'), 'rb') as f:
    graph_def = tf.GraphDef()
    graph_def.ParseFromString(f.read())
    _ = tf.import_graph_def(graph_def, name='')

sess = None
node_lookup = None

def run_inference_on_image(image_data):
  """Runs inference on an image.
  Args:
    image_data: Image data.
  Returns:
    Nothing
  """
  
  # Runs the softmax tensor by feeding the image_data as input to the graph.
  softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
  predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})
  predictions = np.squeeze(predictions)

  # sort the predictions
  top_k = predictions.argsort()[-FLAGS.num_top_predictions:][::-1]

  # map to the friendly names and return the tuples
  return [(node_lookup.id_to_string(node_id), float(predictions[node_id])) for node_id in top_k]



if __name__ == '__main__':

  create_graph()
  print("Model loaded")
  app.run()
  
