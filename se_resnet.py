import torch
from torch import nn
import math
from se_block import SE_block

def se_resnet50(pretrained=False, num_classes=10, model_path='model.pkl'):
    """build a se_resnet50 model
    args:
        pretrained(bool):if true, returns a model pretrained on ImageNet
    """
    layers = [3, 4, 6, 3]
    model = SE_ResNet(layers, num_classes, model_path)
    if pretrained:
        checkpoint = torch.load(model_path)
        model.load_state_dict(checkpoint['model'].state_dict())
    return model
def se_resnet101(pretrained=False, num_classes=10, model_path='model.pkl'):
    """build a se_resnet101 model
    args:
        pretrained(bool):if true, returns a model pretrained on ImageNet
    """
    layers = [3, 4, 23, 3]
    model = SE_ResNet(layers, num_classes, model_path)
    if pretrained:
        checkpoint = torch.load(model.model_path)
        model.load_state_dict(checkpoint['model'].state_dict())
    return model

def se_resnet152(pretrained=False, num_classes=10, model_path='model.pkl'):
    """build a se_resnet152 model
    args:
        pretrained(bool):if true, returns a model pretrained on ImageNet
    """
    layers = [3, 8, 36, 3]
    model = SE_ResNet(layers, num_classes, model_path)
    if pretrained:
        checkpoint = torch.load(model.model_path)
        model.load_state_dict(checkpoint['model'].state_dict())
    return model



class SE_ResNet(nn.Module):
    """ResNet"""
    def __init__(self, layers, num_classes, model_path = 'model.pkl'):
        super(SE_ResNet, self).__init__()
        self.inplanes = 64
        self.model_path = model_path
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=64, kernel_size=7, stride=2, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        self.stack1 = self.make_stack(64, layers[0])
        self.stack2 = self.make_stack(128, layers[1], stride=2)
        self.stack3 = self.make_stack(256, layers[2], stride=2)
        self.stack4 = self.make_stack(512, layers[3], stride=2)
        self.avgpool = nn.AvgPool2d(kernel_size=7, stride=1)
        self.fc = nn.Linear(512 * Bottleneck.expansion, num_classes)
        # init params
        self.init_param()
    def init_param(self):
        """parameter initalization"""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                m.weight.data.normal_(0, math.sqrt(2. / n))
            elif isinstance(m, nn.BatchNorm2d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()
            elif isinstance(m, nn.Linear):
                n = m.weight.shape[0] * m.weight.shape[1]
                m.weight.data.normal_(0, math.sqrt(2./n))
                m.bias.data.zero_()
    def make_stack(self, planes, blocks, stride=1):
        """make stack"""
        downsample=None
        layers = []
        if stride != 1 or self.inplanes != planes * Bottleneck.expansion:
            downsample = nn.Sequential(
                nn.Conv2d(self.inplanes, planes * Bottleneck.expansion, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(planes * Bottleneck.expansion)
            )
        layers.append(Bottleneck(self.inplanes, planes, stride, downsample))
        self.inplanes = planes * Bottleneck.expansion
        for i in range(1, blocks):
            layers.append(Bottleneck(self.inplanes, planes))
        return nn.Sequential(*layers)
    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.stack1(x)
        x = self.stack2(x)
        x = self.stack3(x)
        x = self.stack4(x)
        # x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

class Bottleneck(nn.Module):
    expansion = 4
    def __init__(self, inplanes, planes, stride=1, downsample=None):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2d(inplanes, planes, kernel_size=1, bias=False)
        self.bn1 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv3 = nn.Conv2d(planes, planes * 4, kernel_size=1, bias=False)
        self.bn3 = nn.BatchNorm2d(planes * 4)
        self.selayer = SE_block(planes * 4)
        self.relu = nn.ReLU(inplace=True)
        self.downsample = downsample
        self.stride = stride
    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)
        out = self.selayer(out)
        if self.downsample is not None:
            residual = self.downsample(x)
        out += residual
        out = self.relu(out)
        return out