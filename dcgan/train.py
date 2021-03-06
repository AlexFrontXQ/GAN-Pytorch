import os
import numpy as np

import torch

from torch.autograd import Variable
from torchvision.utils import save_image

from config import parse_args
from dataloader import mnist_loader
from model import Generator, Discriminator, weights_init_normal


def train():
    os.makedirs("images", exist_ok=True)
    os.makedirs("checkpoints", exist_ok=True)

    cuda = True if torch.cuda.is_available() else False
    Tensor = torch.cuda.FloatTensor if cuda else torch.FloatTensor

    # get configs and dataloader
    opt = parse_args()
    data_loader = mnist_loader(opt)

    # Initialize generator and discriminator
    generator = Generator(opt)
    discriminator = Discriminator(opt)

    # Loss function
    adversarial_loss = torch.nn.BCELoss()

    if cuda:
        generator.cuda()
        discriminator.cuda()
        adversarial_loss.cuda()

    # Initialize weights
    generator.apply(weights_init_normal)
    discriminator.apply(weights_init_normal)

    # Optimizers
    optimizer_G = torch.optim.Adam(generator.parameters(), lr=opt.lr, betas=(opt.b1, opt.b2))
    optimizer_D = torch.optim.Adam(discriminator.parameters(), lr=opt.lr, betas=(opt.b1, opt.b2))

    for epoch in range(opt.epochs):
        for i, (imgs, _) in enumerate(data_loader):

            # Adversarial ground truths
            valid = Variable(Tensor(imgs.size(0), 1).fill_(1.0), requires_grad=False)
            fake = Variable(Tensor(imgs.size(0), 1).fill_(0.0), requires_grad=False)

            # Configure input
            z = Variable(Tensor(np.random.normal(0, 1, (imgs.shape[0], opt.latent_dim))))
            real_imgs = Variable(imgs.type(Tensor))
            gen_imgs = generator(z)

            # ------------------
            # Train Discriminator
            # ------------------

            optimizer_D.zero_grad()

            real_loss = adversarial_loss(discriminator(real_imgs), valid)
            fake_loss = adversarial_loss(discriminator(gen_imgs.detach()), fake)
            d_loss = (real_loss + fake_loss) / 2

            d_loss.backward()
            optimizer_D.step()

            # ------------------
            # Train Generator
            # ------------------

            if i % opt.n_critic == 0:
                optimizer_G.zero_grad()

                # Loss for generator
                g_loss = adversarial_loss(discriminator(gen_imgs), valid)

                # Update parameters
                g_loss.backward()
                optimizer_G.step()

            # ------------------
            # Log Information
            # ------------------

            print("[Epoch %d/%d] [Batch %d/%d] [D loss: %f] [G loss: %f]" %
                  (epoch, opt.epochs, i, len(data_loader), d_loss.item(), g_loss.item()))

            batches_done = epoch * len(data_loader) + i
            if batches_done % opt.sample_interval == 0:
                save_image(gen_imgs.data[:25], "images/%d.png" % batches_done, nrow=5, normalize=True)

            if batches_done % opt.checkpoint_interval == 0:
                torch.save(generator.state_dict(), "checkpoints/generator_%d.pth" % epoch)
                # torch.save(discriminator.state_dict(), "checkpoints/discriminator_%d.pth" % epoch)

    torch.save(generator.state_dict(), "checkpoints/generator_done.pth")
    print("Training Process has been Done!")


if __name__ == '__main__':
    train()
