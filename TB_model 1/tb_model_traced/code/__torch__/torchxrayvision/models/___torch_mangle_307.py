class _Transition(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  norm : __torch__.torch.nn.modules.batchnorm.___torch_mangle_303.BatchNorm2d
  relu : __torch__.torch.nn.modules.activation.___torch_mangle_304.ReLU
  conv : __torch__.torch.nn.modules.conv.___torch_mangle_305.Conv2d
  pool : __torch__.torch.nn.modules.pooling.___torch_mangle_306.AvgPool2d
  def forward(self: __torch__.torchxrayvision.models.___torch_mangle_307._Transition,
    argument_1: Tensor) -> Tensor:
    pool = self.pool
    conv = self.conv
    relu = self.relu
    norm = self.norm
    _0 = (relu).forward((norm).forward(argument_1, ), )
    _1 = (pool).forward((conv).forward(_0, ), )
    return _1
