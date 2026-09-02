class Conv2d(Module):
  __parameters__ = ["weight", ]
  __buffers__ = []
  weight : Tensor
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.conv.Conv2d,
    img: Tensor) -> Tensor:
    weight = self.weight
    input = torch._convolution(img, weight, None, [2, 2], [3, 3], [1, 1], False, [0, 0], 1, False, False, True, True)
    return input
