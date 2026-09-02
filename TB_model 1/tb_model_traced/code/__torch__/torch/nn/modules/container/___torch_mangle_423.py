class Sequential(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  __annotations__["0"] = __torch__.torch.nn.modules.linear.Linear
  __annotations__["1"] = __torch__.torch.nn.modules.activation.___torch_mangle_422.ReLU
  __annotations__["2"] = __torch__.torch.nn.modules.dropout.Dropout
  def forward(self: __torch__.torch.nn.modules.container.___torch_mangle_423.Sequential,
    meta: Tensor) -> Tensor:
    _2 = getattr(self, "2")
    _1 = getattr(self, "1")
    _0 = getattr(self, "0")
    _3 = (_1).forward((_0).forward(meta, ), )
    return (_2).forward(_3, )
