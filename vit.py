
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.chdir(r"C:/Users/newon/Downloads/vision transformer in python tensorflow")

import tensorflow as tf
from tensorflow.keras.layers import *
from tensorflow.keras.models import Model

class ClassToken(Layer):
    def __init__(self):
        super().__init__()

    def build(self, input_shape):
        w_init = tf.random_normal_initializer()
        self.w = tf.Variable(
            initial_value = w_init(shape=(1, 1, input_shape[-1]), dtype=tf.float32),
            trainable = True
        )

    def call(self, inputs):
        batch_size = tf.shape(inputs)[0]
        hidden_dim = self.w.shape[-1]

        cls = tf.broadcast_to(self.w, [batch_size, 1, hidden_dim]) # change the shape
        cls = tf.cast(cls, dtype=inputs.dtype) # change the datatype
        return cls

def mlp(x, cf):
    x = Dense(cf["mlp_dim"], activation="gelu")(x)
    x = Dropout(cf["dropout_rate"])(x)
    x = Dense(cf["hidden_dim"])(x)
    x = Dropout(cf["dropout_rate"])(x)
    return x

def transformer_encoder(x, cf):
    skip_1 = x
    x = LayerNormalization()(x)
    x = MultiHeadAttention(num_heads=cf["num_heads"], key_dim=cf["hidden_dim"])(x, x)
    x = Add()([x, skip_1])

    skip_2 = x
    x = LayerNormalization()(x)
    x = mlp(x, cf)
    x = Add()([x, skip_2])

    return x

def ViT(cf):
    
    """ Inputs """
    input_shape = (cf["num_patches"], cf["patch_size"]*cf["patch_size"]*cf["num_channels"])
    print("input_shape",input_shape)
    inputs = Input(input_shape)     ## (None, 64, 1875)

    """ Patch + Position Embeddings """
    patch_embed = Dense(cf["hidden_dim"])(inputs)   ## (None, 64, 768)
    print("patch_embed",patch_embed.shape)
    positions = tf.range(start=0, limit=cf["num_patches"], delta=1)
    #print("positions",positions)
    pos_embed = Embedding(input_dim=cf["num_patches"], output_dim=cf["hidden_dim"])(positions) ## (64, 768)
    print("pos_embed",pos_embed.shape)
    embed = patch_embed + pos_embed ## (None, 64, 768)
    print("embed",embed.shape)
    
    
    """ Adding Class Token """
    token = ClassToken()(embed)
    print("token",token.shape)
    x = Concatenate(axis=1)([token, embed]) ## (None, 64, 768) # 65+1 token patch and 768 reduced dim
    print("x",x.shape)
    for _ in range(cf["num_layers"]):
        x = transformer_encoder(x, cf)

    """ Classification Head """
    x = LayerNormalization()(x)     ## (None, 65, 768)
    x = x[:, 0, :]
    x = Dense(cf["num_classes"], activation="softmax")(x)

    model = Model(inputs, x)
    return model


if __name__ == "__main__":
    config = {}
    config["num_layers"] = 12
    config["hidden_dim"] = 768
    config["mlp_dim"] = 3072
    config["num_heads"] = 12
    config["dropout_rate"] = 0.1
    config["num_patches"] = 64
    config["patch_size"] = 25
    config["num_channels"] = 3
    config["num_classes"] = 5

    model = ViT(config)
    model.summary()
