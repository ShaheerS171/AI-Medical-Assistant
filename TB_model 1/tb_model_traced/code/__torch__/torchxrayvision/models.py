class DenseNet(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  features : __torch__.torch.nn.modules.container.Sequential
  classifier : __torch__.torch.nn.modules.linear.Identity
  def forward(self: __torch__.torchxrayvision.models.DenseNet,
    img: Tensor) -> Tensor:
    classifier = self.classifier
    features = self.features
    input = torch.relu_((features).forward(img, ))
    _0 = torch.adaptive_avg_pool2d(input, [1, 1])
    _1 = ops.prim.NumToTensor(torch.size(input, 0))
    img_feat = torch.view(_0, [int(_1), -1])
    _2 = (classifier).forward()
    return img_feat
class _DenseBlock(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  denselayer1 : __torch__.torchxrayvision.models._DenseLayer
  denselayer2 : __torch__.torchxrayvision.models.___torch_mangle_12._DenseLayer
  denselayer3 : __torch__.torchxrayvision.models.___torch_mangle_19._DenseLayer
  denselayer4 : __torch__.torchxrayvision.models.___torch_mangle_26._DenseLayer
  denselayer5 : __torch__.torchxrayvision.models.___torch_mangle_33._DenseLayer
  denselayer6 : __torch__.torchxrayvision.models.___torch_mangle_40._DenseLayer
  def forward(self: __torch__.torchxrayvision.models._DenseBlock,
    argument_1: Tensor) -> Tensor:
    denselayer6 = self.denselayer6
    denselayer5 = self.denselayer5
    denselayer4 = self.denselayer4
    denselayer3 = self.denselayer3
    denselayer2 = self.denselayer2
    denselayer1 = self.denselayer1
    _3 = (denselayer2).forward((denselayer1).forward(argument_1, ), )
    _4 = (denselayer4).forward((denselayer3).forward(_3, ), )
    _5 = (denselayer6).forward((denselayer5).forward(_4, ), )
    return _5
class _DenseLayer(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  norm1 : __torch__.torch.nn.modules.batchnorm.___torch_mangle_0.BatchNorm2d
  relu1 : __torch__.torch.nn.modules.activation.___torch_mangle_1.ReLU
  conv1 : __torch__.torch.nn.modules.conv.___torch_mangle_2.Conv2d
  norm2 : __torch__.torch.nn.modules.batchnorm.___torch_mangle_3.BatchNorm2d
  relu2 : __torch__.torch.nn.modules.activation.___torch_mangle_4.ReLU
  conv2 : __torch__.torch.nn.modules.conv.___torch_mangle_5.Conv2d
  def forward(self: __torch__.torchxrayvision.models._DenseLayer,
    argument_1: Tensor) -> Tensor:
    conv2 = self.conv2
    relu2 = self.relu2
    norm2 = self.norm2
    conv1 = self.conv1
    relu1 = self.relu1
    norm1 = self.norm1
    _6 = (relu1).forward((norm1).forward(argument_1, ), )
    _7 = (norm2).forward((conv1).forward(_6, ), )
    _8 = (conv2).forward((relu2).forward(_7, ), )
    return torch.cat([argument_1, _8], 1)
class _Transition(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  norm : __torch__.torch.nn.modules.batchnorm.___torch_mangle_41.BatchNorm2d
  relu : __torch__.torch.nn.modules.activation.___torch_mangle_42.ReLU
  conv : __torch__.torch.nn.modules.conv.___torch_mangle_43.Conv2d
  pool : __torch__.torch.nn.modules.pooling.AvgPool2d
  def forward(self: __torch__.torchxrayvision.models._Transition,
    argument_1: Tensor) -> Tensor:
    pool = self.pool
    conv = self.conv
    relu = self.relu
    norm = self.norm
    _9 = (relu).forward((norm).forward(argument_1, ), )
    _10 = (pool).forward((conv).forward(_9, ), )
    return _10
