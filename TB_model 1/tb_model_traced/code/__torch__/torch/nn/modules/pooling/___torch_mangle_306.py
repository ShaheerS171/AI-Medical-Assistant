class AvgPool2d(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.pooling.___torch_mangle_306.AvgPool2d,
    argument_1: Tensor) -> Tensor:
    input = torch.avg_pool2d(argument_1, [2, 2], [2, 2], [0, 0])
    return input
