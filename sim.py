from enum import Enum
import json

base_string = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def to_base(number, base):
    result = ""
    while number:
        result += base_string[number % base]
        number //= base
    ret = result[::-1] or "0"
    return ret.rjust(10,'0')

def load_cards():
    ret = []
    with open('cards.json') as f:
        cards = json.load(f)
    pos = 0
    for card in cards:
        oc = card
        i = card.find(':')
        index = int(card[:i])              
        card = card[i+1:]
        num_free = int(card[-1])
        if num_free==0:
            num_free = 10
        ends = []
        for i in range(14,19):
            ends.append(int(card[i]))
        card = card[:13].replace('-','')
        # print('>>', index, card, num_free, ends)

        # Must be given in order
        pos += 1
        if index!=pos:
            raise Exception(f'Expected index {pos} but got {index}: {oc}')  

        # Always 8 marbles
        cnt = 0
        for i in ends:
            cnt += i
        if cnt != 8:
            raise Exception(f'Ends do not total 8: {oc}')
        
        # Fixed set of tiles
        t = card.upper()
        t = ''.join(sorted(t))
        if t != 'BBBOORRRYY':
            raise Exception(f'Invalid tile configuration: {oc}')
        
        # Count the free tiles
        challenge = ''
        lower_cnt = 0
        for i in card:
            if i in 'bory':
                lower_cnt += 1
                challenge += '*'
            else:
                challenge += i
        
        if lower_cnt != num_free:
            raise Exception(f'Sanity check -- incorrect number of lowers: {oc}')
        
        rep = card
        for e in ends:
            rep += str(e)
        ret.append({
            'index':index,
            'card':card,
            'num_free':num_free,
            'ends':ends, 
            'repr':rep
        })
    return ret


def is_game_valid(s):
    m = to_base(s,4)
    if m.count('0') != 3:
        return None
    if m.count('1') != 3:
        return None
    if m.count('2') != 2:
        return None
    if m.count('3') != 2:
        return None
    return m

# 3333333333(b4) -> 1048575(b10)
MAX_10_DIGIT = 1048575

class NodeType(Enum):
    STRAIGHT = 0  # Blue (3)
    CROSS = 1     # Red (3)
    LEFT = 2      # Yellow (2)
    RIGHT = 3     # Orange (2)
    END = 4       # These are the collection zones

class Node:

    def __init__(self, name):
        self.name = name  # For debugging
        self.node_type = None   
        self.count = 0     
        self.left_out = None
        self.right_out = None
    
    def __repr__(self):
        return f'Name={self.name} type={self.node_type} count={self.count}'

    def get_end_node(self, from_left_right):
        # print(f'>>> Entering {self} from {from_left_right}')
        if self.node_type == NodeType.END:
            return self
        
        elif self.node_type==NodeType.STRAIGHT:
            # Straight down ... left in to left out, right in to right out
            if from_left_right=='left':
                next_node = self.left_out
            else:
                next_node = self.right_out
        elif self.node_type==NodeType.CROSS:
            # Cross over ... left in to right out, right in to left out
            if from_left_right=='left':
                next_node = self.right_out
            else:
                next_node = self.left_out
        elif self.node_type==NodeType.LEFT:
            # Both inputs go to left out
            next_node = self.left_out
        elif self.node_type==NodeType.RIGHT:
            # Both inputs go to right out
            next_node = self.right_out
        else:
            raise Exception(f'Unexpected node type {self.node_type}')
        
        # Recurse into next node
        return next_node[0].get_end_node(next_node[1])
        

def mirror(board):
    # TODO we have to mirror the ends too!
    #     0      |     0
    #    1 2     |    2 1
    #   3 5 6    |   5 4 3
    #  6 7 8 9   |  9 8 7 6
    # a b c d e  | e d c b a
    #
    # 1023456789 | 0215439876-edcba
    return board[0]+board[2]+board[1]+board[5]+board[4]+board[3]+board[9]+board[8]+board[7]+board[6]    

def boards(check_valid=True, check_mirror=True):
    prev = set()
    for i in range(MAX_10_DIGIT):
        m = is_game_valid(i)
        if check_valid and not m:
            continue
        if m in prev:
            continue
        prev.add(m)
        if check_mirror:
            mi = mirror(m)
            if mi in prev:
                continue
            prev.add(mi)
        yield i

def count_valids():    
    cnt = 0
    for _ in boards():
        cnt += 1
    print(cnt)

# 15 processors
processors = []
for i in range(15):
    processors.append(Node(i))

# Wire up the processing nodes
processors[0].left_out = (processors[1], 'right')
processors[0].right_out = (processors[2], 'left')
processors[1].left_out = (processors[3], 'right')
processors[1].right_out = (processors[4], 'left')
processors[2].left_out = (processors[4], 'right')
processors[2].right_out = (processors[5], 'left')
processors[3].left_out = (processors[6], 'right')
processors[3].right_out = (processors[7], 'left')
processors[4].left_out = (processors[7], 'right')
processors[4].right_out = (processors[8], 'left')
processors[5].left_out = (processors[8], 'right')
processors[5].right_out = (processors[9], 'left')
processors[6].left_out = (processors[10], 'right')
processors[6].right_out = (processors[11], 'left')
processors[7].left_out = (processors[11], 'right')
processors[7].right_out = (processors[12], 'left')
processors[8].left_out = (processors[12], 'right')
processors[8].right_out = (processors[13], 'left')
processors[9].left_out = (processors[13], 'right')
processors[9].right_out = (processors[14], 'left')

# Flag the collection processors
outputs = []
for i in range(5):
    outputs.append(processors[i+10])
    processors[i+10].node_type = NodeType.END    

inputs = [
    (processors[6],'left'),
    (processors[3],'left'),
    (processors[1],'left'),
    (processors[0],'left'),
    (processors[0],'right'),
    (processors[2],'right'),
    (processors[5],'right'),
    (processors[9],'right'),    
]

MAP_TYPE = {
    'B' : NodeType.STRAIGHT,
    'R' : NodeType.CROSS,
    'Y' : NodeType.LEFT,
    'O' : NodeType.RIGHT,
}

def configure_processors_base4(num):
    num = to_base(num,4)
    for i in range(10):
        processors[i].node_type = NodeType(int(num[i]))
    for i in range(5):
        outputs[i].count = 0    

def configure_processors(map):    
    map = map.upper().replace('-','')
    for i in range(10):
        processors[i].node_type = MAP_TYPE[map[i]]
    for i in range(5):
        outputs[i].count = 0

def _nr(node):
    if node.node_type == NodeType.STRAIGHT:
        return 'B'
    elif node.node_type == NodeType.CROSS:
        return 'R'
    elif node.node_type == NodeType.LEFT:
        return 'Y'
    elif node.node_type == NodeType.RIGHT:
        return 'O'
    else:
        return '?'
    
def get_number():
    num = ''
    for i in range(10):
        num = num + str(processors[i].node_type.value)
    return int(num,4)
    
def get_representation():
    ret = f'{_nr(processors[0])}-{_nr(processors[1])}{_nr(processors[2])}-{_nr(processors[3])}{_nr(processors[4])}{_nr(processors[5])}-{_nr(processors[6])}{_nr(processors[7])}{_nr(processors[8])}{_nr(processors[9])}-'
    for n in outputs:
        ret = ret + str(n.count)
    return ret

def run_marbles():
    for n in inputs:
        co = n[0].get_end_node(n[1])
        co.count += 1

def does_match(challenge, solution):
    challenge = challenge.replace('-','')
    solution = solution.replace('-','')
    challenge = challenge[:15]
    challenge = challenge.replace('o','*')
    challenge = challenge.replace('y','*')
    challenge = challenge.replace('b','*')
    challenge = challenge.replace('r','*')    
    for i in range(len(solution)):
        if challenge[i]=='*':
            continue
        if challenge[i]!=solution[i]:
            return False
    return True

# a = does_match('Y-br-ROO-ByBR-12311-8','Y-BR-ROO-BYBR-12311')
# print(a)

CHALLENGES = load_cards()



for ch in CHALLENGES:
    configure_processors(ch['card'])
    num = get_number()  
    if is_game_valid(num) is None:
        raise Exception(f'Not a valid challenge: {ch}')

solutions = {}
for i in range(64):
    solutions[i+1] = []

end_counts = [
    [],[],[],[],[]
]

for i in boards(check_mirror=False):
    val = ''    
    configure_processors_base4(i)
    run_marbles()
    g = get_representation()

    for pos in range(5):
        v = outputs[pos].count
        if v not in end_counts[pos]:
            end_counts[pos].append(v)
    
    for ch in CHALLENGES:
        if does_match(ch['repr'],g):
            solutions[ch['index']].append(repr(ch)+' '+g)

for i in range(64):
    print(solutions[i+1])

for ec in end_counts:
    print(sorted(ec))

            



# # configure_processors_base4(0)
# configure_processors('Y-br-ROO-ByBR-12311-8')
# run_marbles()

# outs = []
# for n in outputs:
#     outs.append(n.count)
# print(outs)

# print(get_representation())

# QUESTIONS

# Configurations:
#   - with only tiles given OR with 10 of each tile
#   - allowing mirrors OR ignoring mirrors
# How many unique challenges are there? What other cards were left out?
# How many total boards?
# What's the most marbles that can end up in any given slot?
# How many possible ends are there?
# Does any challenge have multiple solutions?