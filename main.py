import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)
    dg = tf.get_default_graph()
    input_tensor = dg.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob_tensor = dg.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3_out_tensor = dg.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4_out_tensor = dg.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7_out_tensor = dg.get_tensor_by_name(vgg_layer7_out_tensor_name)

    print("input_tensor", tf.shape(input_tensor))
    print("keep_prob_tensor", tf.shape(keep_prob_tensor))
    print("layer3_out_tensor", layer3_out_tensor)
    print("layer4_out_tensor", tf.shape(layer4_out_tensor))
    print("layer7_out_tensor", tf.shape(layer7_out_tensor))
    
    return input_tensor, keep_prob_tensor, layer3_out_tensor, layer4_out_tensor, layer7_out_tensor

tests.test_load_vgg(load_vgg, tf)

def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    t1 = tf.layers.conv2d_transpose(vgg_layer7_out, 512, 3, strides=(2, 2), padding='same', activation=tf.nn.relu, name='t1')
    # t1 has same dimensions as vgg_layer_4; so we can add the latter (skip connection)
    t1 = tf.add(t1, vgg_layer4_out, name='t1_skip')
    
    t2 = tf.layers.conv2d_transpose(t1, 256, 3, strides=(2, 2), padding='same', activation=tf.nn.relu, name='t2')
    # t2 has same dimensions as vgg_layer_3; so we can add the latter (skip connection)
    t2 = tf.add(t2, vgg_layer3_out, name='t2_skip')
    
    t3 = tf.layers.conv2d_transpose(t2, 128, 6, strides=(2, 2), padding='same', activation=tf.nn.relu, name='t3')
    t4 = tf.layers.conv2d_transpose(t3, 64, 12, strides=(2, 2), padding='same', activation=tf.nn.softsign, name='t4')
    t5 = tf.layers.conv2d_transpose(t4, num_classes, 24, strides=(2, 2), padding='same', name='t5')
    print(t1.name, t2.name, t3.name, t4.name, t5.name)
    return t5
tests.test_layers(layers)

def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function
    logits = tf.reshape(nn_last_layer, [-1, num_classes])
    cl = tf.reshape(correct_label, [-1, num_classes])
    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=cl)
    cross_entropy_loss = tf.reduce_mean(cross_entropy)
    train_op = tf.train.AdamOptimizer(learning_rate).minimize(cross_entropy_loss)    
    return logits, train_op, cross_entropy_loss
tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function
    for epoch in range(epochs):
        batch = 0
        for image,label in get_batches_fn(batch_size):
            out, loss = sess.run([train_op, cross_entropy_loss], 
                                 feed_dict={input_image: image, 
                                            correct_label: label, 
                                            keep_prob: 0.5, 
                                            learning_rate: 1e-5})
            print('Epoch ',epoch, ' Batch ',batch,' Loss ',loss)
            batch = batch + 1
tests.test_train_nn(train_nn)


def run():
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        input_tensor, keep_prob_tensor, layer3_out_tensor, layer4_out_tensor, layer7_out_tensor = load_vgg(sess, vgg_path)
        out_tensor = layers(layer3_out_tensor, layer4_out_tensor, layer7_out_tensor, num_classes)
        correct_label = tf.placeholder(tf.int32, [None, None, None, num_classes])
        learning_rate = tf.placeholder(tf.float32)
        logits, train_op, cross_entropy_loss = optimize(out_tensor, correct_label, learning_rate, num_classes)
        sess.run(tf.global_variables_initializer())

        # TODO: Train NN using the train_nn function
        epochs = 20
        batch_size = 2
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_tensor, 
                 correct_label, keep_prob_tensor, learning_rate)

        # TODO: Save inference data using helper.save_inference_samples
        #  helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob_tensor, input_tensor)

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
