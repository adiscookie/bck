# const gemstones = [
#   "Blue Sapphire (Neelam)",
#   "Cat's Eye (Lehsunia)",
#   "Emerald (Panna)",
#   "Hessonite (Gomed)",
#   "Opal",
#   "Pearl",
#   "Red Coral (Moonga)",
#   "Ruby (Manik)",
#   "Yellow Sapphire (Pukhraj)",
#   "Vedic Gemstones",
#   "Amethyst (Katela)",
#   "Blue Zircon",
#   "Citrine (Sunela)",
#   "Iolite (Kaka Nili)",
#   "Peridot",
#   "Pitambari / Neelambari",
#   "White Coral (Moonga)",
#   "White Sapphire",
#   "White Zircon",
#   "Exclusive Gemstones",
#   "Ametrine",
#   "Aquamarine",
#   "Blue Topaz",
#   "Diamond",
#   "Pink Sapphire",
#   "Purple Sapphire",
#   "Star Ruby",
#   "Star Sapphire",
#   "Tanzanite",
#   "Other Gemstones",
#   "Amber",
#   "Heliodor",
#   "Moonstone",
#   "Morganite",
#   "Red Garnet",
#   "Smoky Quartz",
#   "Tourmaline",
#   "Turquoise (Firoza)",
#   "White Topaz",
# ];

# const data = [
#   {
#     gemstone: "Blue Sapphire (Neelam)",
#     suitableFor: ["Saturn"],
#   },
#   {
#     gemstone: "Cat's Eye (Lehsunia)",
#     suitableFor: ["Ketu"],
#   },
#   {
#     gemstone: "Emerald (Panna)",
#     suitableFor: ["Mercury"],
#   },
#   {
#     gemstone: "Hessonite (Gomed)",
#     suitableFor: ["Rahu"],
#   },
#   {
#     gemstone: "Opal",
#     suitableFor: ["Venus"], // Traditional association; may vary
#   },
#   {
#     gemstone: "Pearl",
#     suitableFor: ["Moon"],
#   },
#   {
#     gemstone: "Red Coral (Moonga)",
#     suitableFor: ["Mars"],
#   },
#   {
#     gemstone: "Ruby (Manik)",
#     suitableFor: ["Sun"],
#   },
#   {
#     gemstone: "Yellow Sapphire (Pukhraj)",
#     suitableFor: ["Jupiter"],
#   },
#   {
#     gemstone: "Amethyst (Katela)",
#     suitableFor: ["Saturn"], // Sometimes used as an alternative for Mercury
#   },
#   {
#     gemstone: "Blue Zircon",
#     suitableFor: ["Saturn"],
#   },
#   {
#     gemstone: "Citrine (Sunela)",
#     suitableFor: ["Sun", "Jupiter"],
#   },
#   {
#     gemstone: "Iolite (Kaka Nili)",
#     suitableFor: [], // No standard association found
#   },
#   {
#     gemstone: "Peridot",
#     suitableFor: ["Mercury", "Venus"], // Varies by tradition
#   },
#   {
#     gemstone: "Pitambari / Neelambari",
#     suitableFor: ["Jupiter"], // Often considered a variant of Yellow Sapphire
#   },
#   {
#     gemstone: "White Coral (Moonga)",
#     suitableFor: [], // No standard association found
#   },
#   {
#     gemstone: "White Sapphire",
#     suitableFor: ["Venus", "Saturn"], // Varies by tradition
#   },
#   {
#     gemstone: "White Zircon",
#     suitableFor: [], // No standard association found
#   },
#   {
#     gemstone: "Ametrine",
#     suitableFor: ["Sun", "Saturn"], // Combination of Amethyst and Citrine
#   },
#   {
#     gemstone: "Aquamarine",
#     suitableFor: ["Mercury"], // Varies by tradition
#   },
#   {
#     gemstone: "Blue Topaz",
#     suitableFor: ["Saturn", "Jupiter"], // Varies by tradition
#   },
#   {
#     gemstone: "Diamond",
#     suitableFor: ["Venus"],
#   },
#   {
#     gemstone: "Pink Sapphire",
#     suitableFor: ["Venus", "Saturn"], // Varies by tradition
#   },
#   {
#     gemstone: "Purple Sapphire",
#     suitableFor: ["Saturn", "Ketu"], // Varies by tradition
#   },
#   {
#     gemstone: "Star Ruby",
#     suitableFor: ["Sun"],
#   },
#   {
#     gemstone: "Star Sapphire",
#     suitableFor: ["Saturn"],
#   },
#   {
#     gemstone: "Tanzanite",
#     suitableFor: [], // No standard association found
#   },
#   {
#     gemstone: "Amber",
#     suitableFor: ["Sun"],
#   },
#   {
#     gemstone: "Heliodor",
#     suitableFor: [], // No standard association found
#   },
#   {
#     gemstone: "Moonstone",
#     suitableFor: ["Moon"],
#   },
#   {
#     gemstone: "Morganite",
#     suitableFor: [], // No standard association found
#   },
#   {
#     gemstone: "Red Garnet",
#     suitableFor: ["Mars", "Sun"], // Varies by tradition
#   },
#   {
#     gemstone: "Smoky Quartz",
#     suitableFor: [], // No standard association found
#   },
#   {
#     gemstone: "Tourmaline",
#     suitableFor: [], // No standard association found
#   },
#   {
#     gemstone: "Turquoise (Firoza)",
#     suitableFor: ["Mercury", "Saturn"], // Varies by tradition
#   },
#   {
#     gemstone: "White Topaz",
#     suitableFor: ["Venus", "Saturn"], // Varies by tradition
#   },
#   {
#     gemstone: "Vedic Gemstones",
#     suitableFor: [], // Category label; specific gemstones listed above
#   },
#   {
#     gemstone: "Exclusive Gemstones",
#     suitableFor: [], // Category label; specific gemstones listed above
#   },
#   {
#     gemstone: "Other Gemstones",
#     suitableFor: [], // Category label; specific gemstones listed above
#   },
# ];

# gemstones_and_area = {
#   Career: [
#     "Blue Sapphire (Neelam)",
#     "Cat's Eye (Lehsunia)",
#     "Emerald (Panna)",
#     "Hessonite (Gomed)",
#     "Red Coral (Moonga)",
#     "Ruby (Manik)",
#     "Yellow Sapphire (Pukhraj)",
#     "Amethyst (Katela)",
#     "Blue Zircon",
#     "Citrine (Sunela)",
#     "Peridot",
#     "Pitambari / Neelambari",
#     "White Sapphire",
#     "Ametrine",
#     "Aquamarine",
#     "Blue Topaz",
#     "Pink Sapphire",
#     "Purple Sapphire",
#     "Star Ruby",
#     "Star Sapphire",
#     "Amber",
#     "Turquoise (Firoza)",
#     "White Topaz",
#   ],
#   Love: [
#     "Emerald (Panna)",
#     "Opal",
#     "Pearl",
#     "Red Coral (Moonga)",
#     "Peridot",
#     "White Sapphire",
#     "Aquamarine",
#     "Pink Sapphire",
#     "Diamond",
#     "Moonstone",
#     "Red Garnet",
#     "White Topaz",
#   ],
#   Family: [
#     "Pearl",
#     "Yellow Sapphire (Pukhraj)",
#     "Pitambari / Neelambari",
#     "Blue Topaz",
#     "Diamond",
#     "Moonstone",
#   ],
#   Social: [
#     "Emerald (Panna)",
#     "Hessonite (Gomed)",
#     "Opal",
#     "Yellow Sapphire (Pukhraj)",
#     "Peridot",
#     "Aquamarine",
#     "Pink Sapphire",
#     "Turquoise (Firoza)",
#   ],
#   Self: [
#     "Blue Sapphire (Neelam)",
#     "Cat's Eye (Lehsunia)",
#     "Emerald (Panna)",
#     "Pearl",
#     "Ruby (Manik)",
#     "Amethyst (Katela)",
#     "Blue Zircon",
#     "Citrine (Sunela)",
#     "Pitambari / Neelambari",
#     "White Sapphire",
#     "Ametrine",
#     "Blue Topaz",
#     "Purple Sapphire",
#     "Star Ruby",
#     "Star Sapphire",
#     "Amber",
#     "Moonstone",
#     "Turquoise (Firoza)",
#     "White Topaz",
#   ],
# };
