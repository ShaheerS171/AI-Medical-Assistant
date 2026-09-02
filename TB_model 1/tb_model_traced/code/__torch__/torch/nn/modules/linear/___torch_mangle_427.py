class Linear(Module):
  __parameters__ = ["weight", "bias", ]
  __buffers__ = []
  weight : Tensor
  bias : Tensor
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.linear.___torch_mangle_427.Linear,
    argument_1: Tensor) -> Tensor:
    bias = self.bias
    weight = self.weight
    _0 = torch.linear(argument_1, weight, bias)
    return _0
