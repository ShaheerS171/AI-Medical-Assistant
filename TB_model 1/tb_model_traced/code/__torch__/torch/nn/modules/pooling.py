class MaxPool2d(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.pooling.MaxPool2d,
    argument_1: Tensor) -> Tensor:
    input = torch.max_pool2d(argument_1, [3, 3], [2, 2], [1, 1], [1, 1])
    return input
class AvgPool2d(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.pooling.AvgPool2d,
    argument_1: Tensor) -> Tensor:
    input = torch.avg_pool2d(argument_1, [2, 2], [2, 2], [0, 0])
    return input
