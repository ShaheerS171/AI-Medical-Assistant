class Dropout(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  def forward(self: __torch__.torch.nn.modules.dropout.___torch_mangle_426.Dropout,
    argument_1: Tensor) -> Tensor:
    input = torch.dropout(argument_1, 0.29999999999999999, False)
    return input
