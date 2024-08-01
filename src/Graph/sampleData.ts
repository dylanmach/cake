import { SectionLabel, Preferences } from '../types'
import { Result } from './algorithm/types'

export const sampleLabels2Flavor: SectionLabel[] = [
  {
    id: 0,
    name: 'vanilla',
    color: '#F2F1A1',
    start: 0,
    end: 1,
  },
  {
    id: 1,
    name: 'chocolate',
    color: '#A57C52',
    start: 1,
    end: 2,
  },
]

export const sampleLabels3Flavor: SectionLabel[] = [
  {
    name: 'Strawberry',
    start: 0,
    end: 1,
    color: '#F2CADF',
    id: 1,
  },
  {
    name: 'Vanilla',
    start: 1,
    end: 2,
    color: '#F2F1A1',
    id: 2,
  },
  {
    name: 'Chocolate',
    start: 2,
    end: 3,
    color: '#A57C52',
    id: 3,
  },
]

export const samplePrefs2Flavor2People: Preferences = [
  [
    {
      start: 0,
      startValue: 5,
      end: 1,
      endValue: 5,
      id: 5,
    },
    {
      start: 1,
      startValue: 0.000001,
      end: 2,
      endValue: 0.000001,
      id: 6,
    },
  ],
  [
    {
      start: 0,
      startValue: 0.000001,
      end: 1,
      endValue: 0.000001,
      id: 7,
    },
    {
      start: 1,
      startValue: 5,
      end: 2,
      endValue: 5,
      id: 8,
    },
  ],
  [
    {
      start: 0,
      startValue: 5,
      end: 2,
      endValue: 5,
      id: 9,
    },
  ],
]

export const sampleLabelsPiecewiseConstant: SectionLabel[] = [
  {
    name: 'Strawberry',
    start: 0,
    end: 1,
    color: '#F2CADF',
    id: 1,
  },
  {
    name: 'Vanilla',
    start: 1,
    end: 2,
    color: '#F2F1A1',
    id: 2,
  },
  {
    name: 'Chocolate',
    start: 2,
    end: 3,
    color: '#A57C52',
    id: 3,
  },
  {
    name: 'Blueberry',
    start: 3,
    end: 4,
    color: '#4307f6',
    id: 4,
  },
  {
    name: 'Lime',
    start: 4,
    end: 5,
    color: '#53f507',
    id: 5,
  },
]

export const sample3PersonResults: Result = {
  solution: [
    {
      owner: 0,
      percentValues: [0.37777777777777777, 0.4074074074074074, 0.3481481481481481],
      edges: [
        [0, 0.08888888888888886],
        [0.6666666666666666, 1.3333333333333333],
      ],
    },
    {
      owner: 1,
      percentValues: [0.24444444444444446, 0.4074074074074074, 0.08148148148148147],
      edges: [
        [0.17777777777777773, 0.2666666666666666],
        [0.2666666666666666, 0.6666666666666666],
      ],
    },
    {
      owner: 2,
      percentValues: [0.3777777777777778, 0.18518518518518517, 0.5703703703703705],
      edges: [
        [0.08888888888888886, 0.17777777777777773],
        [1.3333333333333333, 2],
      ],
    },
  ],
  steps: [
    {
      actor: 0,
      action: 'divides the resource into thirds at 33.3% and 66.7%',
      pieces: [
        {
          start: 0,
          end: 0.6666666666666666,
          values: [3.333333333333333, 6.666666666666666, 1.3333333333333333],
          id: 1,
        },
        {
          start: 0.6666666666666666,
          end: 1.3333333333333333,
          values: [3.333333333333333, 4, 3.999999999999999],
          id: 2,
        },
        {
          start: 1.3333333333333333,
          end: 2,
          values: [3.333333333333334, 1.3333333333333335, 6.666666666666668],
          id: 3,
        },
      ],
      assign: false,
    },
    {
      actor: 1,
      action:
        'trims off part of piece 1 to make it the same value as piece 2. The trimmings are set aside',
      pieces: [
        {
          start: 0,
          end: 0.2666666666666666,
          values: [1.333333333333333, 2.666666666666666, 0.5333333333333332],
          note: 'trimming',
          id: 4,
        },
        {
          start: 0.2666666666666666,
          end: 0.6666666666666666,
          values: [1.333333333333333, 2.666666666666666, 0.5333333333333332],
          note: 'trimmed',
          id: 1,
        },
      ],
      assign: false,
    },
    {
      actor: 2,
      action: 'chooses piece 3',
      pieces: [
        {
          start: 1.3333333333333333,
          end: 2,
          values: [3.333333333333334, 1.3333333333333335, 6.666666666666668],
          id: 3,
        },
      ],
      assign: true,
    },
    {
      actor: 1,
      action: 'trimmed piece 1 earlier, because it still remains they must choose it',
      pieces: [
        {
          start: 0.2666666666666666,
          end: 0.6666666666666666,
          values: [2, 4, 0.8],
          note: 'trimmed',
          id: 1,
        },
      ],
      assign: true,
    },
    {
      actor: 0,
      action: 'chooses remaining piece',
      pieces: [
        {
          start: 0.6666666666666666,
          end: 1.3333333333333333,
          values: [3.333333333333333, 4, 3.999999999999999],
          id: 2,
        },
      ],
      assign: true,
    },
    {
      actor: 2,
      action: 'did not choose the trimmed piece earlier so gets to divide the trimmings',
      pieces: [
        {
          start: 0,
          end: 0.2666666666666666,
          values: [1.333333333333333, 2.666666666666666, 0.5333333333333332],
          note: 'trimming',
          id: 4,
        },
      ],
      assign: false,
    },
    {
      actor: 2,
      action: 'divides the trimmings into thirds at 4.44% and 8.89%',
      pieces: [
        {
          start: 0,
          end: 0.08888888888888886,
          values: [0.4444444444444443, 0.8888888888888886, 0.17777777777777773],
          note: 'trimming',
          id: 1,
        },
        {
          start: 0.08888888888888886,
          end: 0.17777777777777773,
          values: [0.4444444444444443, 0.8888888888888886, 0.17777777777777773],
          note: 'trimming',
          id: 2,
        },
        {
          start: 0.17777777777777773,
          end: 0.2666666666666666,
          values: [0.4444444444444444, 0.8888888888888888, 0.17777777777777776],
          note: 'trimming',
          id: 3,
        },
      ],
      assign: false,
    },
    {
      actor: 1,
      action: 'chooses trimming 3',
      pieces: [
        {
          start: 0.17777777777777773,
          end: 0.2666666666666666,
          values: [0.4444444444444444, 0.8888888888888888, 0.17777777777777776],
          note: 'trimming',
          id: 3,
        },
      ],
      assign: true,
    },
    {
      actor: 0,
      action: 'chooses trimming 1',
      pieces: [
        {
          start: 0,
          end: 0.08888888888888886,
          values: [0.4444444444444443, 0.8888888888888886, 0.17777777777777773],
          note: 'trimming',
          id: 1,
        },
      ],
      assign: true,
    },
    {
      actor: 2,
      action: 'chooses remaining trimming',
      pieces: [
        {
          start: 0.08888888888888886,
          end: 0.17777777777777773,
          values: [0.4444444444444443, 0.8888888888888886, 0.17777777777777773],
          note: 'trimming',
          id: 2,
        },
      ],
      assign: true,
    },
  ],
}

export const sampleBranzeiNisanResults: Result = {
  solution: [
    {
      owner: 0,
      percentValues: [0.4192496182353621, 0.39041642191278686, 0.4480828145579374],
      edges: [
        [0.6240001762485008, 1.462499412719225],
      ],
    },
    {
      owner: 1,
      percentValues: [0.3120000881242504, 0.5200001468737506, 0.10400002937475013],
      edges: [
        [0, 0.6240001762485008],
      ],
    },
    {
      owner: 2,
      percentValues: [0.2687502936403875, 0.0895834312134625, 0.44791715606731247],
      edges: [
        [1.462499412719225, 2],
      ],
    },
  ],
  steps: [
    {
        "actor": 2,
        "action": "divides the resource into thirds at 60.0% and 80.0%. The other agents\n            prefer piece 1, so the algorithm begins reducing its size",
        "pieces": [
            {
                "start": 0,
                "end": 1.1999998092651367,
                "values": [
                    5.999999046325684,
                    10.399999618530273,
                    3.999998092651367
                ],
                "id": 1
            },
            {
                "start": 1.1999998092651367,
                "end": 1.5999994277954102,
                "values": [
                    1.9999980926513672,
                    0.7999992370605469,
                    3.9999961853027344
                ],
                "id": 2
            },
            {
                "start": 1.5999994277954102,
                "end": 2,
                "values": [
                    2.000002861022949,
                    0.8000011444091797,
                    4.000005722045898
                ],
                "id": 3
            }
        ],
        "assign": false
    },
    {
        "actor": 4,
        "action": "terminates at the approximately envy-free division at slices 31.2% and 73.1%",
        "pieces": [
            {
                "start": 0,
                "end": 0.6240001762485008,
                "values": [
                    3.120000881242504,
                    6.240001762485008,
                    1.2480003524970016
                ],
                "id": 1
            },
            {
                "start": 0.6240001762485008,
                "end": 1.462499412719225,
                "values": [
                    4.192496182353621,
                    4.6849970629534425,
                    5.376993774695249
                ],
                "id": 2
            },
            {
                "start": 1.462499412719225,
                "end": 2,
                "values": [
                    2.6875029364038747,
                    1.07500117456155,
                    5.375005872807749
                ],
                "id": 3
            }
        ],
        "assign": false
    },
    {
        "actor": 1,
        "action": "is assigned piece 1",
        "pieces": [
            {
                "start": 0,
                "end": 0.6240001762485008,
                "values": [
                    3.120000881242504,
                    6.240001762485008,
                    1.2480003524970016
                ],
                "id": 1
            }
        ],
        "assign": true
    },
    {
        "actor": 0,
        "action": "is assigned piece 2",
        "pieces": [
            {
                "start": 0.6240001762485008,
                "end": 1.462499412719225,
                "values": [
                    4.192496182353621,
                    4.6849970629534425,
                    5.376993774695249
                ],
                "id": 2
            }
        ],
        "assign": true
    },
    {
        "actor": 2,
        "action": "is assigned piece 3",
        "pieces": [
            {
                "start": 1.462499412719225,
                "end": 2,
                "values": [
                    2.6875029364038747,
                    1.07500117456155,
                    5.375005872807749
                ],
                "id": 3
            }
        ],
        "assign": true
    }
]
}

export const samplePiecewiseConstantResults: Result = {
  solution: [
      {
          "owner": 0,
          "percentValues": [
              0.375,
              0.4791666666666665,
              0.4166666666666667
          ],
          "edges": [
              [
                  2.2500000000000004,
                  4.5
              ]
          ]
      },
      {
          "owner": 1,
          "percentValues": [
              0.25,
              0.4791666666666668,
              0.16666666666666666
          ],
          "edges": [
              [
                  0,
                  2.2500000000000004
              ]
          ]
      },
      {
          "owner": 2,
          "percentValues": [
              0.375,
              0.041666666666666664,
              0.4166666666666667
          ],
          "edges": [
              [
                  4.5,
                  5
              ]
          ]
      }
  ],
    
  steps: [
    {
        "actor": 4,
        "action": "first divides the resource into segments",
        "pieces": [
            {
                "start": 0,
                "end": 1,
                "values": [
                    2,
                    10,
                    2
                ],
                "id": 0
            },
            {
                "start": 2,
                "end": 4,
                "values": [
                    0,
                    12,
                    0
                ],
                "id": 1
            },
            {
                "start": 4,
                "end": 5,
                "values": [
                    6,
                    2,
                    10
                ],
                "id": 2
            }
        ],
        "assign": false
    },
    {
        "actor": 4,
        "action": "identifies the segment containing the first cut as 1 and \n                the segment containing the second cut as 2",
        "pieces": [
            {
                "start": 2,
                "end": 4,
                "values": [
                    0,
                    12,
                    0
                ],
                "id": 1
            },
            {
                "start": 4,
                "end": 5,
                "values": [
                    6,
                    2,
                    10
                ],
                "id": 2
            }
        ],
        "assign": false
    },
    {
        "actor": 4,
        "action": "finds an approximately envy-free division at slices 45.0% and 90%",
        "pieces": [
            {
                "start": 0,
                "end": 2.2500000000000004,
                "values": [
                    2,
                    11.500000000000004,
                    2
                ],
                "id": 1
            },
            {
                "start": 2.2500000000000004,
                "end": 4.5,
                "values": [
                    3,
                    11.499999999999996,
                    5
                ],
                "id": 2
            },
            {
                "start": 4.5,
                "end": 5,
                "values": [
                    3,
                    1,
                    5
                ],
                "id": 3
            }
        ],
        "assign": false
    },
    {
        "actor": 1,
        "action": "is assigned piece 1",
        "pieces": [
            {
                "start": 0,
                "end": 2.2500000000000004,
                "values": [
                    2,
                    11.500000000000004,
                    2
                ],
                "id": 1
            }
        ],
        "assign": true
    },
    {
        "actor": 0,
        "action": "is assigned piece 2",
        "pieces": [
            {
                "start": 2.2500000000000004,
                "end": 4.5,
                "values": [
                    3,
                    11.499999999999996,
                    5
                ],
                "id": 2
            }
        ],
        "assign": true
    },
    {
        "actor": 2,
        "action": "is assigned piece 3",
        "pieces": [
            {
                "start": 4.5,
                "end": 5,
                "values": [
                    3,
                    1,
                    5
                ],
                "id": 3
            }
        ],
        "assign": true
    }
]
}
export const sample4PersonResults: Result = {
  solution: [
    {
        "owner": 0,
        "percentValues": [
            0.280639127851233,
            0.17462531441412912,
            0.11641687627608609,
            0.1727894797954852
        ],
        "edges": [
            [
                0,
                0.5238759432423874
            ]
        ]
    },
    {
        "owner": 1,
        "percentValues": [
            0.2334136475673612,
            0.4508663451749867,
            0.30057756344999115,
            0.27564319511629726
        ],
        "edges": [
            [
                0.5238759432423874,
                1.584316652511565
            ]
        ]
    },
    {
        "owner": 2,
        "percentValues": [
            0.20530809673014203,
            0.28719568320380684,
            0.35017180772171674,
            0.27569277069949555
        ],
        "edges": [
            [
                1.584316652511565,
                2.4761240567575364
            ]
        ]
    },
    {
        "owner": 3,
        "percentValues": [
            0.2806391278512638,
            0.08731265720707726,
            0.23283375255220604,
            0.275874554388722
        ],
        "edges": [
            [
                2.4761240567575364,
                3
            ]
        ]
    }
  ],
  
  steps: [
    {
        "actor": 0,
        "action": "divides the resource into quarters at 15.1%, 50.0%, and \n          84.9%",
        "pieces": [
            {
                "start": 0,
                "end": 0.45169820543090056,
                "values": [
                    3.0014918370787163,
                    2.710189232585403,
                    1.8067928217236022,
                    2.557165780993281
                ],
                "id": 1
            },
            {
                "start": 0.45169820543090056,
                "end": 1.4999999999998836,
                "values": [
                    2.998508162921051,
                    7.78981076741355,
                    5.193207178275699,
                    4.755334219006282
                ],
                "id": 2
            },
            {
                "start": 1.4999999999998836,
                "end": 2.5483017945690363,
                "values": [
                    2.9985081629211825,
                    6.144905383708156,
                    7.386414356552988,
                    5.5785804832699055
                ],
                "id": 3
            },
            {
                "start": 2.5483017945690363,
                "end": 3,
                "values": [
                    3.00149183707905,
                    1.3550946162928912,
                    3.61358564344771,
                    4.1089195167305315
                ],
                "id": 4
            }
        ],
        "assign": false
    },
    {
        "actor": 4,
        "action": "terminates at the approximately envy-free division at slices 17.5%, 52.8%, and \n            82.5%. This division satisfies condition B",
        "pieces": [
            {
                "start": 0,
                "end": 0.5238759432423874,
                "values": [
                    3.367669534214796,
                    3.1432556594543244,
                    2.0955037729695496,
                    2.9374211565232486
                ],
                "id": 1
            },
            {
                "start": 0.5238759432423874,
                "end": 1.584316652511565,
                "values": [
                    2.8009637708083344,
                    8.11559421314976,
                    5.410396142099841,
                    4.685934316977053
                ],
                "id": 2
            },
            {
                "start": 1.584316652511565,
                "end": 2.4761240567575364,
                "values": [
                    2.463697160761704,
                    5.169522297668523,
                    6.303092538990901,
                    4.686777101891424
                ],
                "id": 3
            },
            {
                "start": 2.4761240567575364,
                "end": 3,
                "values": [
                    3.367669534215166,
                    1.5716278297273907,
                    4.1910075459397085,
                    4.689867424608273
                ],
                "id": 4
            }
        ],
        "assign": false
    },
    {
        "actor": 0,
        "action": "is indifferent between slices 1 and 4",
        "pieces": [
            {
                "start": 0,
                "end": 0.5238759432423874,
                "values": [
                    3.367669534214796,
                    3.1432556594543244,
                    2.0955037729695496,
                    2.9374211565232486
                ],
                "id": 1
            },
            {
                "start": 2.4761240567575364,
                "end": 3,
                "values": [
                    3.367669534215166,
                    1.5716278297273907,
                    4.1910075459397085,
                    4.689867424608273
                ],
                "id": 4
            }
        ],
        "assign": false
    },
    {
        "actor": 3,
        "action": "is indifferent between slices 2 and 3. These\n            slices are each weakly preferred by at least one other agent",
        "pieces": [
            {
                "start": 0.5238759432423874,
                "end": 1.584316652511565,
                "values": [
                    2.8009637708083344,
                    8.11559421314976,
                    5.410396142099841,
                    4.685934316977053
                ],
                "id": 2
            },
            {
                "start": 1.584316652511565,
                "end": 2.4761240567575364,
                "values": [
                    2.463697160761704,
                    5.169522297668523,
                    6.303092538990901,
                    4.686777101891424
                ],
                "id": 3
            }
        ],
        "assign": false
    },
    {
        "actor": 0,
        "action": "is assigned piece 1",
        "pieces": [
            {
                "start": 0,
                "end": 0.5238759432423874,
                "values": [
                    3.367669534214796,
                    3.1432556594543244,
                    2.0955037729695496,
                    2.9374211565232486
                ],
                "id": 1
            }
        ],
        "assign": true
    },
    {
        "actor": 1,
        "action": "is assigned piece 2",
        "pieces": [
            {
                "start": 0.5238759432423874,
                "end": 1.584316652511565,
                "values": [
                    2.8009637708083344,
                    8.11559421314976,
                    5.410396142099841,
                    4.685934316977053
                ],
                "id": 2
            }
        ],
        "assign": true
    },
    {
        "actor": 2,
        "action": "is assigned piece 3",
        "pieces": [
            {
                "start": 1.584316652511565,
                "end": 2.4761240567575364,
                "values": [
                    2.463697160761704,
                    5.169522297668523,
                    6.303092538990901,
                    4.686777101891424
                ],
                "id": 3
            }
        ],
        "assign": true
    },
    {
        "actor": 3,
        "action": "is assigned piece 4",
        "pieces": [
            {
                "start": 2.4761240567575364,
                "end": 3,
                "values": [
                    3.367669534215166,
                    1.5716278297273907,
                    4.1910075459397085,
                    4.689867424608273
                ],
                "id": 4
            }
        ],
        "assign": true
    }
  ],
}