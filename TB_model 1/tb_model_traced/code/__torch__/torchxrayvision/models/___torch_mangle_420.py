class _DenseBlock(Module):
  __parameters__ = []
  __buffers__ = []
  training : bool
  _is_full_backward_hook : Optional[bool]
  denselayer1 : __torch__.torchxrayvision.models.___torch_mangle_314._DenseLayer
  denselayer2 : __torch__.torchxrayvision.models.___torch_mangle_321._DenseLayer
  denselayer3 : __torch__.torchxrayvision.models.___torch_mangle_328._DenseLayer
  denselayer4 : __torch__.torchxrayvision.models.___torch_mangle_335._DenseLayer
  denselayer5 : __torch__.torchxrayvision.models.___torch_mangle_342._DenseLayer
  denselayer6 : __torch__.torchxrayvision.models.___torch_mangle_349._DenseLayer
  denselayer7 : __torch__.torchxrayvision.models.___torch_mangle_356._DenseLayer
  denselayer8 : __torch__.torchxrayvision.models.___torch_mangle_363._DenseLayer
  denselayer9 : __torch__.torchxrayvision.models.___torch_mangle_370._DenseLayer
  denselayer10 : __torch__.torchxrayvision.models.___torch_mangle_377._DenseLayer
  denselayer11 : __torch__.torchxrayvision.models.___torch_mangle_384._DenseLayer
  denselayer12 : __torch__.torchxrayvision.models.___torch_mangle_391._DenseLayer
  denselayer13 : __torch__.torchxrayvision.models.___torch_mangle_398._DenseLayer
  denselayer14 : __torch__.torchxrayvision.models.___torch_mangle_405._DenseLayer
  denselayer15 : __torch__.torchxrayvision.models.___torch_mangle_412._DenseLayer
  denselayer16 : __torch__.torchxrayvision.models.___torch_mangle_419._DenseLayer
  def forward(self: __torch__.torchxrayvision.models.___torch_mangle_420._DenseBlock,
    argument_1: Tensor) -> Tensor:
    denselayer16 = self.denselayer16
    denselayer15 = self.denselayer15
    denselayer14 = self.denselayer14
    denselayer13 = self.denselayer13
    denselayer12 = self.denselayer12
    denselayer11 = self.denselayer11
    denselayer10 = self.denselayer10
    denselayer9 = self.denselayer9
    denselayer8 = self.denselayer8
    denselayer7 = self.denselayer7
    denselayer6 = self.denselayer6
    denselayer5 = self.denselayer5
    denselayer4 = self.denselayer4
    denselayer3 = self.denselayer3
    denselayer2 = self.denselayer2
    denselayer1 = self.denselayer1
    _0 = (denselayer2).forward((denselayer1).forward(argument_1, ), )
    _1 = (denselayer4).forward((denselayer3).forward(_0, ), )
    _2 = (denselayer6).forward((denselayer5).forward(_1, ), )
    _3 = (denselayer8).forward((denselayer7).forward(_2, ), )
    _4 = (denselayer10).forward((denselayer9).forward(_3, ), )
    _5 = (denselayer12).forward((denselayer11).forward(_4, ), )
    _6 = (denselayer14).forward((denselayer13).forward(_5, ), )
    _7 = (denselayer16).forward((denselayer15).forward(_6, ), )
    return _7
