class _DenseLayer(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  norm1 : __torch__.torch.nn.modules.batchnorm.___torch_mangle_44.BatchNorm2d
  relu1 : __torch__.torch.nn.modules.activation.___torch_mangle_45.ReLU
  conv1 : __torch__.torch.nn.modules.conv.___torch_mangle_46.Conv2d
  norm2 : __torch__.torch.nn.modules.batchnorm.___torch_mangle_47.BatchNorm2d
  relu2 : __torch__.torch.nn.modules.activation.___torch_mangle_48.ReLU
  conv2 : __torch__.torch.nn.modules.conv.___torch_mangle_49.Conv2d
  def forward(self: __torch__.torchxrayvision.models.___torch_mangle_50._DenseLayer,
    argument_1: Tensor) -> Tensor:
    conv2 = self.conv2
    relu2 = self.relu2
    norm2 = self.norm2
    conv1 = self.conv1
    relu1 = self.relu1
    norm1 = self.norm1
    _0 = (relu1).forward((norm1).forward(argument_1, ), )
    _1 = (norm2).forward((conv1).forward(_0, ), )
    _2 = (conv2).forward((relu2).forward(_1, ), )
    return torch.cat([argument_1, _2], 1)
