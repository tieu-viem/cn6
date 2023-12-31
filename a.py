import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import random
import math
import threading
import time
import copy
from PIL import Image, ImageDraw
from tkinter import PhotoImage

C = math.sqrt(2)
#(số playout chạy trong từng bước là bao nhiêu ) xuất ra 10 playout và wi/ni sau 5s thì máy thực hiện được , lưu ván cờ phải theo form chuẩn connect 6
TURN_TIME_LIMIT = 5
DEFAULT_BOARD_SIZE = 19 # giá trị kích thước mặc định

class MCTSNode:
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move  # Lưu trữ nước đi (x, y)
        self.children = []
        self.visits = 0
        self.value = 0  # Giá trị thực tế của nút


class MCTSConnect6Bot:
        def __init__(self, player, board_size):
            self.player = player
            self.board_size = board_size
            self.first_move = True  # Biến theo dõi nước đi đầu tiên
            self.remaining_moves = 0  # Số nước đi còn lại để bot thực hiện
            self.bot_algorithm = "MCTS"
            self.root_node = MCTSNode([0 for _ in range(self.board_size)] for _ in range(self.board_size))  # Khởi tạo nút gốc với trạng thái ban đầu của bàn cờ
            


        def mcts_search(self, board, player):
            # Khởi tạo cây tìm kiếm MCTS với nút gốc là trạng thái hiện tại của bàn cờ
            root_node = MCTSNode(board)

            for _ in range(100):  # Thực hiện 100 lượt chơi mô phỏng (điều chỉnh số lượt cần thiết)
                # 1. Lựa chọn một nút theo chiến lược UCB (Upper Confidence Bound)
                selected_node = self.select_node(root_node)
                if selected_node is None:
                    break
                if not self.is_fully_expanded(selected_node):
                    self.expand_node(selected_node)
                result = self.simulate_game(selected_node, player)
                self.backpropagate(selected_node, result)

            best_child = self.select_best_child(root_node)

            if best_child:
                # Cập nhật trạng thái bàn cờ và thông tin về lượt đi
                board = best_child.state
                self.remaining_moves -= 1
                if self.remaining_moves == 0:
                    self.first_move = True  # Chuyển lượt cho người chơi đánh
                return board, None
            else:
                return board, None

        def make_bot_move(self, max_playouts=100, time_limit=5):
            if self.bot_algorithm == "MCTS" and self.bot_move_in_progress:
                start_time = time.time()
                playouts_done = 0
                playout_ratios = []

                while time.time() - start_time < time_limit and playouts_done < max_playouts:
                    legal_moves = self.get_legal_moves(self.root_node.state)
                    if not legal_moves:
                        break

                    move = random.choice(legal_moves)
                    new_x, new_y = move
                    self.root_node.state[new_y][new_x] = self.current_player
                    self.remaining_moves -= 1

                    result = self.simulate_game(self.root_node, self.current_player)
                    self.backpropagate(self.root_node, result)

                    best_child = self.select_best_child(self.root_node)
                    if best_child:
                        visits = best_child.visits
                        value = best_child.value
                    else:
                        visits = 0
                        value = 0

                    if value != 0:
                        ratio = visits / value
                        playout_ratios.append(ratio)

                    playouts_done += 1

                if self.remaining_moves == 0:
                    self.current_player = 3 - self.current_player
                    self.remaining_moves = 1

                    if self.bot_enabled and self.current_player == self.bot_player and not self.bot.first_move:
                        self.bot_move_in_progress = True

                        best_ratios = sorted(playout_ratios, reverse=True)[:2]
                        best_moves = []

                        for ratio in best_ratios:
                            index = playout_ratios.index(ratio)
                            best_move = legal_moves[index]
                            best_moves.append(best_move)

                        if len(best_moves) >= 2:
                            move1, move2 = best_moves[:2]
                            x1, y1 = move1
                            x2, y2 = move2
                            self.root_node.state[y1][x1] = self.current_player
                            self.root_node.state[y2][x2] = self.current_player
                            self.remaining_moves -= 2

                        playout_ratios = []


            

        def select_node(self, node): #chọn lựa node
            best_child = None
            best_score = -float("inf")
            for child in node.children:
                exploration = C * math.sqrt(math.log(node.visits) / child.visits) #khám phá 
                score = self.evaluate_position(child.state, self.player) + exploration # uct= khai thác + khám phá
                if score > best_score:
                    best_score = score
                    best_child = child
            return best_child # node con tốt nhất

        def is_fully_expanded(self, node): #chọn node mở rộng
            legal_moves = self.get_legal_moves(node.state)
            return len(node.children) == len(legal_moves)

        

        def expand_node(self, node): # mở rộng node
            legal_moves = self.get_legal_moves(node.state)
            for move in legal_moves:
                new_state = [row[:] for row in node.state]
                x, y = move
                new_state[y][x] = self.player
                new_node = MCTSNode(new_state, parent=node)
                node.children.append(new_node)

        

        def backpropagate(self, node, result): # cập nhật lan truyền ngược
            while node is not None:
                node.visits += 1
                node.value += result
                node = node.parent

        def select_best_child(self, node):
            best_child = None
            best_value = -float("inf")
            for child in node.children:
                child_value = child.value / (child.visits + 1e-5)
                if child_value > best_value:
                    best_value = child_value
                    best_child = child
            return best_child

        def get_legal_moves(self, board):
            legal_moves = []
            for y in range(self.board_size):
                for x in range(self.board_size):
                    if board[y][x] == 0:
                        legal_moves.append((x, y))
            return legal_moves

        def simulate_game(self, node, player):
            while True:
                legal_moves = self.get_legal_moves(node.state)
                if not legal_moves:
                    return 0
                move = random.choice(legal_moves)
                x, y = move
                node.state[y][x] = player
                player = 3 - player
                if self.check_win(node.state, x, y):
                    return 1

        def evaluate_position(self, board, player):
            opponent = 3 - player
            player_score = 0
            opponent_score = 0

            for y in range(self.board_size):
                for x in range(self.board_size):
                    if board[y][x] == player:
                        # Kiểm tra hàng ngang (horizontal)
                        if x + 5 < self.board_size:
                            window = board[y][x:x+6]
                            player_count = window.count(player)
                            opponent_count = window.count(opponent)
                            if player_count == 6:
                                player_score += 1000
                            if opponent_count == 6:
                                opponent_score += 1000
                            if player_count == 5 and window.count(0) == 1:
                                player_score += 500
                            if opponent_count == 5 and window.count(0) == 1:
                                opponent_score += 500

                        # Kiểm tra hàng dọc (vertical)
                        if y + 5 < self.board_size:
                            window = [board[y+i][x] for i in range(6)]
                            player_count = window.count(player)
                            opponent_count = window.count(opponent)
                            if player_count == 6:
                                player_score += 1000
                            if opponent_count == 6:
                                opponent_score += 1000
                            if player_count == 5 and window.count(0) == 1:
                                player_score += 500
                            if opponent_count == 5 and window.count(0) == 1:
                                opponent_score += 500

                        # Kiểm tra đường chéo từ trái lên phải (diagonal left to right)
                        if x + 5 < self.board_size and y + 5 < self.board_size:
                            window = [board[y+i][x+i] for i in range(6)]
                            player_count = window.count(player)
                            opponent_count = window.count(opponent)
                            if player_count == 6:
                                player_score += 1000
                            if opponent_count == 6:
                                opponent_score += 1000
                            if player_count == 5 and window.count(0) == 1:
                                player_score += 500
                            if opponent_count == 5 and window.count(0) == 1:
                                opponent_score += 500

                        # Kiểm tra đường chéo từ phải xuống trái (diagonal right to left)
                        if x - 5 >= 0 and y + 5 < self.board_size:
                            window = [board[y+i][x-i] for i in range(6)]
                            player_count = window.count(player)
                            opponent_count = window.count(opponent)
                            if player_count == 6:
                                player_score += 1000
                            if opponent_count == 6:
                                opponent_score += 1000
                            if player_count == 5 and window.count(0) == 1:
                                player_score += 500
                            if opponent_count == 5 and window.count(0) == 1:
                                opponent_score += 500

            return player_score - opponent_score

class Connect6Game: 
    def __init__(self, board_size=19, bot_enabled=True, bot_algorithm="MCTS"):
        self.root = tk.Tk()
        self.root.title("Connect6 Game")
        self.double_move = False  # Bắt đầu với lượt đánh một quân
        self.default_board_size = DEFAULT_BOARD_SIZE
        self.board_size = self.default_board_size
        self.cell_size = 30
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.first_move = True
        self.current_player = 2  # Thay đổi từ 1 (quân đen) thành 2 (quân đỏ)
        self.lock = threading.Lock()
        self.remaining_moves = 1
        self.bot_enabled = False
        self.bot_player = 2
        self.current_turn = 0
        self.bot_thread = None
        self.bot_algorithm = "MCTS"
        self.bot_thinking_time = 3
        self.bot_move_in_progress = False
        self.bot = MCTSConnect6Bot(self.bot_player, self.board_size)  # Tạo một thể hiện của bot ở đây
        self.bot = MCTSConnect6Bot(player=1, board_size=19)
        self.canvas = tk.Canvas(self.root, width=self.board_size * self.cell_size, height=self.board_size * self.cell_size)
        self.canvas.pack()
         
        self.move_counter = 1  # Biến để theo dõi số nước đi
        self.moves_history = {"black": [], "red": []}

        self.setup_menu()
        self.setup_game_mode_selection()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="MENU GAME", menu=file_menu)
        file_menu.add_command(label="Save Moves", command=self.save_moves_to_image)
        file_menu.add_separator()
        
        file_menu.add_command(label="2 player", command=self.start_two_players_game)
        file_menu.add_command(label="vs bot", command=self.start_with_bot_game)
        file_menu.add_command(label="restart game", command=self.restart_game)
        file_menu.add_command(label="exit game", command=self.exit_game)
        file_menu.add_command(label="selection_color", command=self.start_with_bot_game)
    def setup_game_mode_selection(self):
        selection_window = tk.Toplevel(self.root) 
        selection_window.title("BOARD GAME CONNECT 6")
        selection_window.geometry("550x309")

        background_image = PhotoImage(file="1.png")

        background_label = tk.Label(selection_window, image=background_image)
        background_label.place(x=0, y=0, relwidth=1, relheight=1)

        background_label.photo = background_image

        black_button = tk.Button(selection_window, text="Chọn màu Đen", font=("Arial", 14), command=lambda: self.select_color("black"))
        black_button.pack(pady=10)

        red_button = tk.Button(selection_window, text="Chọn màu Đỏ", font=("Arial", 14), command=lambda: self.select_color("red"))
        red_button.pack(pady=10)

        selection_window.resizable(False, False)

    def start_game(self, bot_mode):
        self.bot_enabled = bot_mode == 1
        self.current_turn = 0
        self.root.title("Connect6 Game - Chế độ " + ("2 Người" if bot_mode == 2 else "Đánh với Máy"))
        self.canvas.bind("<Button-1>", lambda event, cell_size=self.cell_size: self.on_cell_click(event.x // cell_size, event.y // cell_size))
        
        # Khởi tạo lại bàn cờ với các ô trống
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        
        if self.bot_enabled and self.current_player == self.bot_player:
            self.start_bot_thread()

        self.draw_board()

    def start_two_players_game(self):
        self.setup_new_game()
        self.start_game(2)
        
        # Đảm bảo rằng bàn cờ được khởi tạo với các ô trống
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]


    def start_bot_thread(self):
        self.bot_thread = threading.Thread(target=self.bot_thread_function)
        self.bot_thread.start()

    def bot_thread_function(self):
        while self.bot_enabled:
            with self.lock:  # Sử dụng lock để đồng bộ hóa
                if self.current_player == self.bot_player and self.remaining_moves > 0:
                    self.bot_move_in_progress = True
                    self.make_bot_move()
            time.sleep(0.1)

    

    def select_color(self, color):
        if color == "black":
            self.bot_player = 1
        else:
            self.bot_player = 2
        self.root.destroy()
        self.setup_new_game()
        self.start_game(1)  # Bắt đầu chế độ đánh với máy


    def start_with_bot_game(self):
        self.setup_new_game()
        self.bot_algorithm = "MCTS"
        self.start_game(1)

        # Kiểm tra nếu bot là người chơi đầu tiên
        if self.bot_enabled and self.bot_player == 1:
            self.bot_move_in_progress = True
            self.bot_algorithm.first_move = False  # Đặt first_move của bot thành False
            self.make_bot_move()


    def setup_new_game(self):
        self.current_player = 1
        self.remaining_moves = 1
        self.bot_enabled = False
        self.current_turn = 0
        self.bot_thread = None
        self.moves_history = {"black": [], "red": []}
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.draw_board()

    def save_moves_to_image(self):
        if not self.moves_history["black"] and not self.moves_history["red"]:
            messagebox.showwarning("Lưu nước đi", "Không có nước đi nào để lưu.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")])
        if file_path:
            board_image = self.create_board_image()
            draw = ImageDraw.Draw(board_image)

            for x, y, move_number in self.moves_history["black"]:  # Giải nén 3 giá trị (x, y, move_number)
                self.draw_move(draw, x, y, "black")
                draw.text((x * self.cell_size, y * self.cell_size), str(move_number), fill="black")

            for x, y, move_number in self.moves_history["red"]:  # Giải nén 3 giá trị (x, y, move_number)
                self.draw_move(draw, x, y, "red")
                draw.text((x * self.cell_size, y * self.cell_size), str(move_number), fill="black")

            board_image.save(file_path, "PNG")
            messagebox.showinfo("Lưu nước đi", f"Nước đi đã được lưu tại {file_path}")


    def change_board_size(self):
        new_size = simpledialog.askinteger("Thay đổi kích thước", "Nhập kích thước mới (ví dụ: 19):", initialvalue=self.board_size)
        if new_size and new_size >= 6:
            self.board_size = new_size
            self.setup_new_game()

    def create_board_image(self):
        board_image = Image.new("RGB", (self.board_size * self.cell_size, self.board_size * self.cell_size), "white")
        draw = ImageDraw.Draw(board_image)

        for y in range(self.board_size):
            for x in range(self.board_size):
                color = "black" if self.board[y][x] == 1 else "red" if self.board[y][x] == 2 else "gray"
                self.draw_move(draw, x, y, color)

        return board_image

    def draw_move(self, draw, x, y, color):
        cell_size = self.cell_size
        padding = 2
        draw.ellipse(
            (x * cell_size + padding, y * cell_size + padding,
             (x + 1) * cell_size - padding, (y + 1) * cell_size - padding),
            fill=color, outline=color)

    def evaluate_position(self, x, y, player):
        opponent = 3 - player
        player_score = 0
        opponent_score = 0

        for dx, dy in [(1, 0), (0, 1)]:
            consecutive_pieces = 0
            for direction in [-1, 1]:
                for i in range(1, 6):
                    new_x = x + i * direction * dx
                    new_y = y + i * direction * dy
                    if 0 <= new_x < self.board_size and 0 <= new_y < self.board_size:
                        if self.board[new_y][new_x] == player:
                            consecutive_pieces += 1
                        else:
                            break
                    else:
                        break
            if consecutive_pieces >= 4:
                player_score += 1000
            elif consecutive_pieces == 3:
                player_score += 100
            elif consecutive_pieces == 2:
                player_score += 10

        for dx, dy in [(1, 1), (1, -1)]:
            consecutive_pieces = 0
            for direction in [-1, 1]:
                for i in range(1, 6):
                    new_x = x + i * direction * dx
                    new_y = y + i * direction * dy
                    if 0 <= new_x < self.board_size and 0 <= new_y < self.board_size:
                        if self.board[new_y][new_x] == player:
                            consecutive_pieces += 1
                        else:
                            break
                    else:
                        break
            if consecutive_pieces >= 4:
                player_score += 1000
            elif consecutive_pieces == 3:
                player_score += 100
            elif consecutive_pieces == 2:
                player_score += 10

        return player_score

    def toggle_bot(self):
        self.bot_enabled = not self.bot_enabled
        if self.bot_enabled:
            self.start_bot_thread()

    def evaluate_board(self, board, player):
        opponent = 3 - player
        player_score = 0
        opponent_score = 0

        for y in range(self.board_size):
            for x in range(self.board_size):
                if board[y][x] == player:
                    player_score += self.evaluate_position(x, y, player)
                elif board[y][x] == opponent:
                    opponent_score += self.evaluate_position(x, y, opponent)

        return player_score - opponent_score

    def on_cell_click(self, x, y):
        if not self.bot_move_in_progress: #bot thực hiện người chơi không thực hiện 
            if 0 <= x < self.board_size and 0 <= y < self.board_size and self.remaining_moves > 0: #Hàm kiểm tra xem người chơi đã nhấp chuột vào một ô hợp lệ trên bàn cờ
                if self.board[y][x] == 0: #Nếu các điều kiện trên đều đúng, hàm tiếp tục kiểm tra ô đã được đánh (có giá trị self.board[y][x]) hoặc chưa.
                    self.board[y][x] = self.current_player #Nếu ô chưa được đánh (giá trị self.board[y][x] == 0), hàm thực hiện các bước sau: người chơi hiện tại đã đánh vào ô đó.
                    self.draw_board() #cập nhật trạng thái hiện tại của bàn cờ và hiển thị nước đi mới.
                    self.record_move(x, y, self.move_counter)  # Truyền số nước đi vào hàm
                    self.move_counter += 1  # Tăng số nước đi lên một đơn vị


                    if self.check_win(x, y): # kiểm tra xem người chơi đã chiến thắng hay chưa bằng cách gọi hàm
                        winner = "Đen" if self.current_player == 1 else "Đỏ"
                        messagebox.showinfo("Kết thúc trò chơi", f"{winner} chiến thắng!")
                        self.save_moves_to_image() 
                    else: #Nếu người chơi chưa chiến thắng, hàm giảm số lượng nước đi còn lại 
                        self.remaining_moves -= 1 
                        if self.remaining_moves == 0: #Nếu self.remaining_moves = 0 người chơi đã đánh xong 1 lượt, nên chuyển lượt cho người chơi khác và thiết lập self.remaining_moves là 2 để cho lượt mới. 
                            self.current_player = 3 - self.current_player #Chuyển lượt cho người chơi khác
                            self.remaining_moves = 2
                            if self.bot_enabled and self.current_player == self.bot_player:
                                self.bot_move_in_progress = True #self.bot_move_in_progress thành True và gọi hàm self.make_bot_move() để bot thực hiện nước đi của mình
                                self.make_bot_move()  # Gọi hàm để bot thực hiện nước đi

                else:
                    if self.board[y][x] == 0: # kiểm tra xem ô mà người chơi đã nhấp chuột vào có giá trị bằng 0 hay không,
                        self.board[y][x] = self.current_player #Gán giá trị của ô đó bằng self.current_player người chơi hiện tại đã đánh vào ô đó.
                        self.draw_board() # cập nhật trạng thái hiện tại của bàn cờ và hiển thị nước đi mới.
                        self.record_move(x, y)
                        self.remaining_moves -= 1 #đi 1 đơn vị.
                        if self.remaining_moves == 0: #Nếu bằng 0 người chơi đã hoàn thành lượt hiện tại
                            self.current_player = 3 - self.current_player #Chuyển lượt cho người chơi khác
                            self.remaining_moves = 2  #2 để bắt đầu lượt mới. Người chơi có 2 nước đi trong lượt mới.
                            if self.bot_enabled and self.current_player == self.bot_player: #Kiểm tra xem chế độ chơi với bot đã được kích hoạt và đến lượt của bot
                                self.bot_move_in_progress = True 
                                self.make_bot_move()

    def check_win(self, x, y):
        directions = [(1, 0), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)] #danh sách các hướng có thể (6 hướng)(dx, dy)

        for dx, dy in directions:
            consecutive_count = 1 #đếm số lượng quân cờ liên tiếp của người chơi hiện tại trong một hướng =1 vì ô (x, y) hiện tại đã được đánh bởi người chơi.

            for i in range(1, 6): # kiểm tra các ô phía sau (x, y) trong hướng đó
                new_x = x + i * dx 
                new_y = y + i * dy

                if not (0 <= new_x < self.board_size) or not (0 <= new_y < self.board_size): # kiểm tra xem có nằm trong bàn cờ
                    break

                if self.board[new_y][new_x] == self.current_player: #giá trị của ô đó có phải là quân cờ của người chơi hiện tại không 
                    consecutive_count += 1 
                else:
                    break

            for i in range(1, 6): #vòng lặp thứ hai kiểm tra các ô phía trước (x, y) trong hướng đó.
                new_x = x - i * dx
                new_y = y - i * dy

                if not (0 <= new_x < self.board_size) or not (0 <= new_y < self.board_size):
                    break

                if self.board[new_y][new_x] == self.current_player:
                    consecutive_count += 1
                else:
                    break

            if consecutive_count >= 6: # 6 quân liên tiếp
                return True # thắng

        return False # thua

    def record_move(self, x, y, move_number=None):  # Thêm giá trị mặc định cho move_number
        current_player_color = "black" if self.current_player == 1 else "red"
        if move_number is not None:
            self.moves_history[current_player_color].append((x, y, move_number))
        else:
            self.moves_history[current_player_color].append((x, y))

    

    

    
            

  
    # Sửa lại hàm make_bot_move
    
    # Cập nhật hàm make_bot_move
    def make_bot_move(self, max_playouts=100, time_limit=5):
        if self.bot_algorithm == "MCTS" and self.bot_move_in_progress:
            start_time = time.time()
            playouts_done = 0
            playout_ratios = []

            while time.time() - start_time < time_limit and playouts_done < max_playouts:
                legal_moves = self.bot.get_legal_moves(self.board)
                if not legal_moves:
                    break

                # Thực hiện MCTS để tính toán nước đi
                selected_move, _, _ = self.bot.mcts_search(self.board, self.current_player)

                # Áp dụng nước đi đã tính toán vào bàn cờ
                x, y = selected_move
                self.board[y][x] = self.current_player
                self.remaining_moves -= 1
                self.draw_board()
                self.record_move(None, None)

                if self.remaining_moves == 0:
                    self.current_player = 3 - self.current_player
                    self.remaining_moves = 2  # Đánh 2 quân đỏ sau khi chuyển lượt

                playouts_done += 1

            if self.remaining_moves == 0:
                self.bot_move_in_progress = False  # Chuyển lượt cho người chơi

    # Cập nhật hàm mcts_search
    def mcts_search(self, board, player, max_playouts=100, time_limit=5):
        # Khởi tạo cây tìm kiếm MCTS với nút gốc là trạng thái hiện tại của bàn cờ
        root_node = MCTSNode(board)

        start_time = time.time()
        playouts_done = 0

        while playouts_done < max_playouts and (time.time() - start_time) < time_limit:
            # 1. Lựa chọn một nút theo chiến lược UCB (Upper Confidence Bound)
            selected_node = self.select_node(root_node)
            if selected_node is None:
                break
            if not self.is_fully_expanded(selected_node):
                self.expand_node(selected_node)
            result = self.simulate_game(selected_node, player)
            self.backpropagate(selected_node, result)
            playouts_done += 1

        best_child = self.select_best_child(root_node)

        if best_child:
            # Cập nhật trạng thái bàn cờ và thông tin về lượt đi
            x, y = best_child.move
            priority = best_child.value / (best_child.visits + 1e-5)
            self.remaining_moves -= 1
            if self.remaining_moves == 0:
                self.first_move = True  # Chuyển lượt cho người chơi đánh
            return x, y, priority
        else:
            return None  # Trả về None nếu không có nước đi tốt nhất nào được tìm thấy



    



            

    def select_node(self, node):
        best_child = None
        best_value = -float("inf")
        for child in node.children:
            exploration = C * math.sqrt(math.log(node.visits) / child.visits)
            # Thay đổi cách tính giá trị của node con
            child_value = child.value / (child.visits + 1e-5)
            score = child_value + exploration
            if score > best_value:
                best_value = score
                best_child = child
        return best_child

    def is_fully_expanded(self, node):
        legal_moves = self.get_legal_moves(node.state)
        return len(node.children) == len(legal_moves)

    def expand_node(self, node):
        legal_moves = self.get_legal_moves(node.state)
        for move in legal_moves:
            new_state = [row[:] for row in node.state]
            x, y = move
            new_state[y][x] = self.current_player
            new_node = MCTSNode(new_state, parent=node, move=move)  # Truyền thông tin nước đi vào nút con
            node.children.append(new_node)

    def backpropagate(self, node, result):
        while node is not None:
            node.visits += 1
            # Cập nhật giá trị của node cha dựa trên giá trị thực tế của node con
            node.value += result
            node = node.parent

    def select_best_child(self, node):
        best_child = None
        best_value = -float("inf")
        for child in node.children:
            # Thay đổi cách tính giá trị của node con
            child_value = child.value / (child.visits + 1e-5)
            if child_value > best_value:
                best_value = child_value
                best_child = child
        return best_child

    def get_legal_moves(self, board):
        legal_moves = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                if board[y][x] == 0:
                    legal_moves.append((x, y))
        return legal_moves

    def simulate_game(self, node, player):
        while True:
            legal_moves = self.get_legal_moves(node.state)
            if not legal_moves:
                return 0
            move = random.choice(legal_moves)
            x, y = move
            node.state[y][x] = player
            player = 3 - player
            if self.check_win(node.state, x, y):
                return 1

    def evaluate_position(self, board, player): # hàm đánh giá kiểm tra chiến thắng
        opponent = 3 - player
        player_score = 0
        opponent_score = 0

        for y in range(self.board_size):
            for x in range(self.board_size):
                if board[y][x] == player:
                    # Kiểm tra hàng ngang (horizontal)
                    if x + 5 < self.board_size:
                        window = board[y][x:x+6]
                        player_count = window.count(player)
                        opponent_count = window.count(opponent)
                        if player_count == 6:
                            player_score += 10000
                        if opponent_count == 6:
                            opponent_score += 10000
                        if player_count == 5 and window.count(0) == 1:
                            player_score += 5000
                        if opponent_count == 5 and window.count(0) == 1:
                            opponent_score += 5000
                        if player_count == 4 and window.count(0) == 2:
                            player_score += 1000
                        if opponent_count == 4 and window.count(0) == 2:
                            opponent_score += 1000

                    # Kiểm tra hàng dọc (vertical)
                    if y + 5 < self.board_size:
                        window = [board[y+i][x] for i in range(6)]
                        player_count = window.count(player)
                        opponent_count = window.count(opponent)
                        if player_count == 6:
                            player_score += 10000
                        if opponent_count == 6:
                            opponent_score += 10000
                        if player_count == 5 and window.count(0) == 1:
                            player_score += 5000
                        if opponent_count == 5 and window.count(0) == 1:
                            opponent_score += 5000
                        if player_count == 4 and window.count(0) == 2:
                            player_score += 1000
                        if opponent_count == 4 and window.count(0) == 2:
                            opponent_score += 1000

                    # Kiểm tra đường chéo từ trái lên phải (diagonal left to right)
                    if x + 5 < self.board_size and y + 5 < self.board_size:
                        window = [board[y+i][x+i] for i in range(6)]
                        player_count = window.count(player)
                        opponent_count = window.count(opponent)
                        if player_count == 6:
                            player_score += 10000
                        if opponent_count == 6:
                            opponent_score += 10000
                        if player_count == 5 and window.count(0) == 1:
                            player_score += 5000
                        if opponent_count == 5 and window.count(0) == 1:
                            opponent_score += 5000
                        if player_count == 4 and window.count(0) == 2:
                            player_score += 1000
                        if opponent_count == 4 and window.count(0) == 2:
                            opponent_score += 1000

                    # Kiểm tra đường chéo từ phải xuống trái (diagonal right to left)
                    if x - 5 >= 0 and y + 5 < self.board_size:
                        window = [board[y+i][x-i] for i in range(6)]
                        player_count = window.count(player)
                        opponent_count = window.count(opponent)
                        if player_count == 6:
                            player_score += 10000
                        if opponent_count == 6:
                            opponent_score += 10000
                        if player_count == 5 and window.count(0) == 1:
                            player_score += 5000
                        if opponent_count == 5 and window.count(0) == 1:
                            opponent_score += 5000
                        if player_count == 4 and window.count(0) == 2:
                            player_score += 1000
                        if opponent_count == 4 and window.count(0) == 2:
                            opponent_score += 1000

        return player_score - opponent_score



    



    def draw_board(self):
        self.canvas.delete("all")
        for y in range(self.board_size):
            for x in range(self.board_size):
                if self.board[y][x] == 1:
                    color = "black"
                elif self.board[y][x] == 2:
                    color = "red"
                else:
                    color = "gray"

                move_number = self.get_move_number(x, y)
                text = str(move_number) if move_number is not None else ""
                self.canvas.create_oval(
                    x * self.cell_size,
                    y * self.cell_size,
                    (x + 1) * self.cell_size,
                    (y + 1) * self.cell_size,
                    fill=color,
                    outline="black"
                )
                self.canvas.create_text(
                    (x + 0.5) * self.cell_size,
                    (y + 0.5) * self.cell_size,
                    text=text,
                    fill="white" if color == "black" else "black"
                )
    def get_move_number(self, x, y):
        for move_info in self.moves_history["black"]:
            if move_info[0] == x and move_info[1] == y:
                return move_info[2]
        for move_info in self.moves_history["red"]:
            if move_info[0] == x and move_info[1] == y:
                return move_info[2]
        return None

    def restart_game(self):
        self.setup_new_game()
        self.move_counter = 1  # Đặt lại số nước đi hiện tại về 1
        self.current_turn = 0  # Đặt lại lượt đi hiện tại về 0
        if self.bot_enabled and self.current_player == self.bot_player:
            self.start_bot_thread()

        # Lặp qua lịch sử nước đi và cập nhật lại số nước đi hiện tại
        for player_moves in self.moves_history.values():
            for move_info in player_moves:
                move_info_index = player_moves.index(move_info)
                if move_info[2] != self.move_counter:
                    player_moves[move_info_index] = (move_info[0], move_info[1], self.move_counter)
                self.move_counter += 1

        self.draw_board()



    def exit_game(self):
        self.root.quit()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    game = Connect6Game()
    game.run()
