class Sequential(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  __annotations__["0"] = __torch__.torch.nn.modules.linear.___torch_mangle_424.Linear
  __annotations__["1"] = __torch__.torch.nn.modules.batchnorm.BatchNorm1d
  __annotations__["2"] = __torch__.torch.nn.modules.activation.___torch_mangle_425.ReLU
  __annotations__["3"] = __torch__.torch.nn.modules.dropout.___torch_mangle_426.Dropout
  __annotations__["4"] = __torch__.torch.nn.modules.linear.___torch_mangle_427.Linear
  def forward(self: __torch__.torch.nn.modules.container.___torch_mangle_428.Sequential,
    input: Tensor) -> Tensor:
    _4 = getattr(self, "4")
    _3 = getattr(self, "3")
    _2 = getattr(self, "2")
    _1 = getattr(self, "1")
    _0 = getattr(self, "0")
    _5 = (_1).forward((_0).forward(input, ), )
    _6 = (_4).forward((_3).forward((_2).forward(_5, ), ), )
    return _6
