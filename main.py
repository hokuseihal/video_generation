import torch
import torch.nn as nn
import torch.nn.functional as F
import utils as U
import torchvision
from torchvision.utils import save_image
from model.dcgan import DCGAN
import core as Co
from dataset import CelebADataset

def operate(phase):
    for i,(noise,realimg )in enumerate(loader):
        B,C,H,W=realimg.shape
        lossDreal,lossDfake,lossG,fake=model.trainbatch(noise,realimg)

        # fid=cal_fid(realimg)
        # IS=cal_is(realimg)
        print(f'{e}/{epoch}:{i}/{len(loader)}, Dreal:{lossDreal}, Dfake:{lossDfake}, G:{lossG}')
        Co.addvalue(writer,'loss:Dreal',lossDreal,e)
        Co.addvalue(writer,'loss:Dfake',lossDfake,e)
        Co.addvalue(writer,'loss:G',lossG,e)
        # Co.addvalue(writer,'fid',fid,e)
        # Co.addvalue(writer,'IS',IS,e)
        if i==0:
            save_image((fake*0.5)+0.5,f'{savefolder}/{e}.png')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--batchsize',default=8,type=int)
    parser.add_argument('--model',default='dcgan')
    parser.add_argument('--dataset',default='celeba')
    parser.add_argument('--optimizer',default='adam')
    parser.add_argument('--zsize',type=int,default=128)
    parser.add_argument('--epoch',default=100,type=int)
    parser.add_argument('--savefolder',default='tmp')
    parser.add_argument('--checkpoint',default=None)
    parser.add_argument('--size',default=128,type=int)
    args=parser.parse_args()
    epoch=args.epoch
    savefolder='data/'+args.savefolder
    import os
    os.makedirs(savefolder,exist_ok=True)
    if args.checkpoint:
        chk=torch.load(args.checkpoint)
        loader=chk['loader']
        model=chk['model']
        e=chk['e']
        writer=chk['writer']
        args=chk['args']
    else:
        lossDreal=lambda x:-U.min(x-1,0)
        lossDfake=lambda x:-U.min(-x-1,0)
        lossG=lambda x:-x
        lossDreal=lambda x:(x-1)**2
        lossDfake=lambda x:x**2
        lossG=lambda x:(x-1)**22
        if args.dataset=='celeba':
            loader=torch.utils.data.DataLoader(CelebADataset(torchvision.datasets.CelebA('/opt/data','all',download=True),args.size,args.zsize),batch_size=args.batchsize,num_workers=4,shuffle=True)
        if args.optimizer=='adam':
            optimizer=torch.optim.Adam
        if args.model == 'dcgan':
            model = DCGAN(optimizerG=optimizer,optimizerD=optimizer,lossDreal=lossDreal,lossDfake=lossDfake,lossG=lossG,zsize=args.zsize)
        writer={}
        e=0
    import json
    with open(f'{savefolder}/args.json','w') as f:
        json.dump(args.__dict__,f)
    for e in range(e,epoch):
        operate('train')
        torch.save({
            'model':model.cpu(),
            'e':e,
            'writer':writer,
            'args':args,
            'loader':loader
        },savefolder+'/chk.pth')