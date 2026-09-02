class Sequential(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  conv0 : __torch__.torch.nn.modules.conv.Conv2d
  norm0 : __torch__.torch.nn.modules.batchnorm.BatchNorm2d
  relu0 : __torch__.torch.nn.modules.activation.ReLU
  pool0 : __torch__.torch.nn.modules.pooling.MaxPool2d
  denseblock1 : __torch__.torchxrayvision.models._DenseBlock
  transition1 : __torch__.torchxrayvision.models._Transition
  denseblock2 : __torch__.torchxrayvision.models.___torch_mangle_128._DenseBlock
  transition2 : __torch__.torchxrayvision.models.___torch_mangle_133._Transition
  denseblock3 : __torch__.torchxrayvision.models.___torch_mangle_302._DenseBlock
  transition3 : __torch__.torchxrayvision.models.___torch_mangle_307._Transition
  denseblock4 : __torch__.torchxrayvision.models.___torch_mangle_420._DenseBlock
  norm5 : __torch__.torch.nn.modules.batchnorm.___torch_mangle_421.BatchNorm2d
  def forward(self: __torch__.torch.nn.modules.container.Sequential,
    img: Tensor) -> Tensor:
    norm5 = self.norm5
    denseblock4 = self.denseblock4
    transition3 = self.transition3
    denseblock3 = self.denseblock3
    transition2 = self.transition2
    denseblock2 = self.denseblock2
    transition1 = self.transition1
    denseblock1 = self.denseblock1
    pool0 = self.pool0
    relu0 = self.relu0
    norm0 = self.norm0
    conv0 = self.conv0
    _0 = (norm0).forward((conv0).forward(img, ), )
    _1 = (pool0).forward((relu0).forward(_0, ), )
    _2 = (transition1).forward((denseblock1).forward(_1, ), )
    _3 = (transition2).forward((denseblock2).forward(_2, ), )
    _4 = (transition3).forward((denseblock3).forward(_3, ), )
    _5 = (norm5).forward((denseblock4).forward(_4, ), )
    return _5
