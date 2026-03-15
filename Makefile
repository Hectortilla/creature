up:
	brew services start postgresql@14
	brew services start redis

down:
	brew services stop postgresql@14
	brew services stop redis