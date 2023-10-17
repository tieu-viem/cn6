
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import random
import math
import threading
import time
import copy
from PIL import Image, ImageDraw
from tkinter import PhotoImage
import pickle
C = math.sqrt(2)
#(số playout chạy trong từng bước là bao nhiêu ) xuất ra 10 playout và wi/ni sau 5s thì máy thực hiện được , lưu ván cờ phải theo form chuẩn connect 6
TURN_TIME_LIMIT = 5
DEFAULT_BOARD_SIZE = 19 # giá trị kích thước mặc định

class MCTSNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = 0



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
        file_menu.add_command(label="Save Moves", command=self.save_game_state)

        file_menu.add_separator()
        
        file_menu.add_command(label="2 player", command=self.start_two_players_game)
        file_menu.add_command(label="vs bot", command=self.start_with_bot_game)
        file_menu.add_command(label="restart game", command=self.restart_game)
        file_menu.add_command(label="exit game", command=self.exit_game)
        file_menu.add_command(label="selection_color", command=self.start_with_bot_game)
        # Khi người dùng nhấn vào tùy chọn "Open Game" trong menu
        file_menu.add_command(label="Open Game", command=self.open_game_state)
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

    def save_game_state(self):
        game_state = {
            "board": self.board,  # Lưu trạng thái bàn cờ
            "moves_history": self.moves_history,  # Lưu lịch sử nước đi
            "current_player": self.current_player,  # Bao gồm cả current_player
            "remaining_moves": self.remaining_moves  # Bao gồm số lượt chơi còn lại
        }
        
        file_path = filedialog.asksaveasfilename(defaultextension=".game", filetypes=[("Game Files", "*.game")])
        
        if file_path:
            with open(file_path, "wb") as file:
                pickle.dump(game_state, file)
                messagebox.showinfo("Lưu trạng thái trò chơi", f"Trạng thái trò chơi đã được lưu tại {file_path}")

    def update_status(self):
        if self.current_player == 1:
            self.status_var.set("Lượt đánh: Đen")
        elif self.current_player == 2:
            self.status_var.set("Lượt đánh: Đỏ")
        else:
            self.status_var.set("Trò chơi kết thúc")

        # Kiểm tra chiến thắng
        winner = self.check_win(self.board, self.last_move[0], self.last_move[1])
        if winner:
            self.status_var.set(f"Trò chơi kết thúc. Người chơi {winner} chiến thắng!")


    def load_game_state(self):
        file_path = filedialog.askopenfilename(filetypes=[("Game Files", "*.game")])
        
        if file_path:
            with open(file_path, "rb") as file:
                game_state = pickle.load(file)
                self.board = game_state["board"]  # Khôi phục trạng thái bàn cờ
                self.moves_history = game_state["moves_history"]  # Khôi phục lịch sử nước đi
                self.draw_board()  # Vẽ lại bàn cờ
                messagebox.showinfo("Tải trạng thái trò chơi", f"Trạng thái trò chơi đã được tải từ {file_path}")

    def open_game_state(self):
        file_path = filedialog.askopenfilename(filetypes=[("Game Files", "*.game")])
        if file_path:
            # Đọc dữ liệu trò chơi từ tệp
            with open(file_path, 'rb') as file:
                game_data = pickle.load(file)

            # Khôi phục trạng thái và lịch sử nước đi
            self.board = game_data["board"]
            self.moves_history = game_data["moves_history"]

            # Cập nhật giao diện người dùng
            self.draw_board()
            self.update_status()  # Gọi phương thức cập nhật trạng thái trò chơi

            # Nếu cần, bắt đầu lại trò chơi từ vị trí đánh hiện tại
            if self.bot_algorithm == "MCTS" and self.current_player == 2:
                self.bot_move_in_progress = True
                self.make_bot_move()





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


                    if self.check_win(self.board, x, y, self.current_player):
                             # kiểm tra xem người chơi đã chiến thắng hay chưa bằng cách gọi hàm
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
    def check_win(self, board, x, y, player):
        directions = [(1, 0), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)]

        for dx, dy in directions:
            consecutive_count = 1

            for i in range(1, 6):
                new_x = x + i * dx
                new_y = y + i * dy

                if not (0 <= new_x < self.board_size) or not (0 <= new_y < self.board_size):
                    break

                if board[new_y][new_x] == player:
                    consecutive_count += 1
                    if consecutive_count >= 6:
                        return True  # Dừng và trả về chiến thắng nếu có ít nhất 6 quân liên tiếp
                else:
                    break

        for dx, dy in directions:
            consecutive_count = 1

            for i in range(1, 6):
                new_x = x - i * dx
                new_y = y - i * dy

                if not (0 <= new_x < self.board_size) or not (0 <= new_y < self.board_size):
                    break

                if board[new_y][new_x] == player:
                    consecutive_count += 1
                    if consecutive_count >= 6:
                        return True  # Dừng và trả về chiến thắng nếu có ít nhất 6 quân liên tiếp
                else:
                    break

        return False






    def record_move(self, x, y, move_number=None):
        current_player_color = "black" if self.current_player == 1 else "red"
        if move_number is not None:
            self.moves_history[current_player_color].append((x, y, move_number))
        else:
            # Tìm số thứ tự tiếp theo cho nước đi
            last_move = self.moves_history[current_player_color][-1] if self.moves_history[current_player_color] else None
            if last_move:
                last_move_number = last_move[2]
                new_move_number = last_move_number + 1
            else:
                new_move_number = 1

            self.moves_history[current_player_color].append((x, y, new_move_number))

    #nước đi bot

    def make_bot_move(self, max_playouts=100, time_limit=5):
        if self.bot_algorithm == "MCTS" and self.bot_move_in_progress:
            start_time = time.time()
            playouts_done = 0
            playout_ratios = []

            while time.time() - start_time < time_limit and playouts_done < 2:
                legal_moves = self.bot.get_legal_moves(self.board)
                if not legal_moves:
                    break

                best_move = None
                best_value = -float("inf")
                block_move = None  # Để lưu trạng thái có thể chặn người chơi

                for move in legal_moves:
                    new_x, new_y = move
                    if new_x is not None and new_y is not None:
                        self.board[new_y][new_x] = self.current_player
                        value = self.evaluate_position(self.board, self.current_player)
                        self.board[new_y][new_x] = 0  # Hoàn trả bàn cờ về trạng thái ban đầu

                        if value > best_value:
                            best_value = value
                            best_move = move

                        if self.check_win(self.board, new_x, new_y, self.current_player):
                            # Lưu nước đi có thể chặn người chơi
                            block_move = move

                if block_move:
                    new_x, new_y = block_move
                    if new_x is not None and new_y is not None:
                        # Đánh 2 quân đỏ để chặn người chơi
                        self.board[new_y][new_x] = 2  # Đánh 2 quân đỏ để chặn
                        self.remaining_moves -= 1
                        self.draw_board()
                        self.record_move(new_x, new_y)

                        if self.check_win(self.board, new_x, new_y, 2):
                            # Thông báo chiến thắng cho bot (quân đỏ)
                            messagebox.showinfo("Kết quả", "Bot (quân đỏ) chiến thắng!")

                elif best_move:
                    new_x, new_y = best_move
                    if new_x is not None and new_y is not None:
                        # Tiếp tục với nước đi tốt nhất
                        self.board[new_y][new_x] = self.current_player
                        self.remaining_moves -= 1
                        self.draw_board()
                        self.record_move(new_x, new_y)

                if self.remaining_moves == 0:
                    self.current_player = 3 - self.current_player
                    self.remaining_moves = 2  # Đánh 2 quân đen sau khi chuyển lượt

                playouts_done += 1

            if playouts_done >= 2:
                self.bot_move_in_progress = False  # Chuyển lượt cho người chơi

            # Kiểm tra chiến thắng của bot (quân đỏ) sau 6 quân đỏ liên tiếp
            for x, y in legal_moves:
                if self.check_win(self.board, x, y, 2):
                    # Thông báo chiến thắng cho bot (quân đỏ)
                    messagebox.showinfo("Kết quả", "Bot (quân đỏ) chiến thắng!")
                    return


    
    def block_player_if_possible(self, board, player):
        directions = [(1, 0), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)]

        for y in range(self.board_size):
            for x in range(self.board_size):
                if board[y][x] == 0:
                    for dx, dy in directions:
                        consecutive_count = 0
                        open_ends = 0
                        blocking_moves = []

                        for i in range(1, 6):
                            new_x = x + i * dx
                            new_y = y + i * dy

                            if not (0 <= new_x < self.board_size) or not (0 <= new_y < self.board_size):
                                break

                            if board[new_y][new_x] == player:
                                consecutive_count += 1
                            elif board[new_y][new_x] == 0:
                                open_ends += 1

                            if consecutive_count == 4 and open_ends == 1:
                                blocking_moves.append((x, y))

                        if blocking_moves:
                            for move_x, move_y in blocking_moves:
                                for i in range(1, 3):
                                    new_x = move_x + i * dx
                                    new_y = move_y + i * dy
                                    if 0 <= new_x < self.board_size and 0 <= new_y < self.board_size and board[new_y][new_x] == 0:
                                        board[new_y][new_x] = 2  # Đánh 2 quân đỏ để chặn
                            return  # Chặn xong, không cần kiểm tra nữa

        return None


    def mcts_choose_best_2_moves(self, max_playouts=100):
        best_moves = []

        for _ in range(2):
            best_move = self.mcts_search(self.board, self.current_player, max_playouts)
            if best_move:
                best_moves.append(best_move)

        return best_moves



    def find_blocking_move(self, board, player):
        # Xác định các nước chiến thắng tiếp theo của người chơi
        winning_moves = self.find_winning_moves(board, player)

        if winning_moves:
            # Nếu có nước đi để chiến thắng, chọn một trong các nước này để chặn
            return winning_moves[0]
        else:
            return None

    def find_winning_moves(self, board, player):
        winning_moves = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                if board[y][x] == 0:
                    # Tạo một bản sao của bàn cờ để kiểm tra các nước đi tiềm năng
                    new_board = [row[:] for row in board]
                    new_board[y][x] = player

                    if self.check_win(new_board, x, y, player):
                        winning_moves.append((x, y))

        return winning_moves



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
            board = best_child.state
            self.remaining_moves -= 1
            if self.remaining_moves == 0:
                self.first_move = True  # Chuyển lượt cho người chơi đánh
            return board, None
        else:
            return board, None

    



            

    def select_node(self, node):
        best_child = None
        best_value = -float("inf")
        for child in node.children:
            exploration = C * math.sqrt(math.log(node.visits) / child.visits)
            # Thay đổi cách tính giá trị của node
            value = child.value / (child.visits + 1e-5)
            score = value + exploration
            if score > best_value:
                best_value = score
                best_child = child
        return best_child


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
        red_moves_done = 0  # Số lượt đã đánh đỏ
        while True:
            legal_moves = self.get_legal_moves(node.state)
            if not legal_moves:
                return 0

            # Chọn 2 nước đi tốt nhất
            best_moves = []
            best_value = -float("inf")
            for move in legal_moves:
                x, y = move
                new_state = [row[:] for row in node.state]
                new_state[y][x] = player
                priority = self.evaluate_position(new_state, player)  # Đánh giá nước đi
                if priority > best_value:
                    best_value = priority
                    best_moves = [move]
                elif priority == best_value:
                    best_moves.append(move)

            # Chọn 2 nước đi tốt nhất
            chosen_moves = best_moves[:2]

            for move in chosen_moves:
                x, y = move
                node.state[y][x] = player
                player = 3 - player

            red_moves_done += len(chosen_moves)

            if red_moves_done >= 2:  # Khi đã đánh 2 quân đỏ
                if self.check_win(node.state, x, y):
                    return 1  # Trả về 1 nếu bot thắng
                return 0  # Trả về 0 nếu hòa hoặc tiếp tục trò chơi


    def evaluate_position(self, board, player):
        directions = [(1, 0), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)]

        total_score = 0

        for y in range(self.board_size):
            for x in range(self.board_size):
                if board[y][x] == 0:
                    for dx, dy in directions:
                        consecutive_count = 0
                        open_ends = 0
                        blocked = False

                        for i in range(1, 6):
                            new_x = x + i * dx
                            new_y = y + i * dy

                            if not (0 <= new_x < self.board_size) or not (0 <= new_y < self.board_size):
                                break

                            if board[new_y][new_x] == player:
                                consecutive_count += 1
                            elif board[new_y][new_x] == 0:
                                open_ends += 1
                            else:
                                blocked = True
                                break

                        if consecutive_count == 5 and open_ends == 1:
                            total_score += 10000
                        elif consecutive_count == 5 and open_ends == 0:
                            total_score += 100000
                        elif consecutive_count == 4 and open_ends == 1 and not blocked:
                            total_score += 1000
                            # Điểm số thêm cho trường hợp chặn
                            # Nếu người chơi đạt 4 quân đen liên tiếp, bot sẽ đánh 2 quân đỏ để chặn
                            if player == 1:
                                total_score += 1000  # Đánh 2 quân đỏ sau 4 quân đen của người chơi
                            elif player == 2:
                                total_score += 1000  # Đánh 2 quân đỏ sau 4 quân đen của người chơi
                        elif consecutive_count == 3 and open_ends == 1 and not blocked:
                            total_score += 100
                        elif consecutive_count == 3 and open_ends == 0 and not blocked:
                            total_score += 1000
                        elif consecutive_count == 2 and open_ends == 1 and not blocked:
                            total_score += 10
                        elif consecutive_count == 2 and open_ends == 0 and not blocked:
                            total_score += 100
                        elif consecutive_count == 1 and open_ends == 1 and not blocked:
                            total_score += 1
                        elif consecutive_count == 5 and open_ends == 2:
                            total_score += 1000000  # Điểm số thêm cho trạng thái có 5 quân liên tiếp của bot
                        # Điểm số thêm cho trường hợp chặn người chơi là quân đen đạt 4 quân liên tiếp
                        if consecutive_count == 4 and open_ends == 1 and not blocked and player == 1:
                            total_score += 1000  # Đánh 2 quân đỏ sau 4 quân đen của người chơi
                        elif consecutive_count == 4 and open_ends == 1 and not blocked and player == 2:
                            total_score += 1000  # Đánh 2 quân đỏ sau 4 quân đen của người chơi

        return total_score








        



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
            if len(move_info) >= 3 and move_info[0] == x and move_info[1] == y:
                return move_info[2]
        for move_info in self.moves_history["red"]:
            if len(move_info) >= 3 and move_info[0] == x and move_info[1] == y:
                return move_info[2]
        return None


    def choose_bot_move(self, all_moves, board):
        # Tìm tất cả các nước đi đã thực hiện bởi người chơi và bot
        all_taken_moves = [move for move in all_moves if board[move[1]][move[0]] in (2, 1)]

        # Tìm nước đi cuối cùng của người chơi
        last_player_move = max([self.get_move_number(x, y) for x, y in all_taken_moves if board[y][x] == 1], default=0)

        # Tìm nước đi tiếp theo cho bot
        next_bot_move_number = last_player_move + 1

        # Chọn nước đi dựa trên số thứ tự mới
        next_bot_move = self.find_move_by_number(all_moves, next_bot_move_number)

        return next_bot_move

    def find_move_by_number(self, all_moves, move_number):
        for move in all_moves:
            if move[2] == move_number:
                return move
        return None  # Trả về None nếu không tìm thấy nước đi với số thứ tự mong muốn

    
    

    

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
