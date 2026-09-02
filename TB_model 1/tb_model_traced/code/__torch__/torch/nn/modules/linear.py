class Identity(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.linear.Identity) -> NoneType:
    return None
class Linear(Module):
  __parameters__ = ["weight", "bias", ]
  __buffers__ = []
  weight : Tensor
  bias : Tensor
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.linear.Linear,
    meta: Tensor) -> Tensor:
    bias = self.bias
    weight = self.weight
    return torch.linear(meta, weight, bias)
